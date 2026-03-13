"""Клиент OpenAI: распознавание текста по фото (два прохода) и проверка диктанта."""

import base64
import json
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI

from src.config import get_settings
from src.prompts import CHECK_DICTATION_PROMPT, OCR_PROMPT
from src.utils.exceptions import DictationProcessingError, OpenAIServiceError

logger = logging.getLogger(__name__)

# Глобальный клиент (инициализируется при первом использовании)
_openai_client: Optional[OpenAI] = None

# Тип результата OCR: dict с keys lines, uncertain_spans, ocr_confidence
OcrResult = Dict[str, Any]


def _get_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        settings = get_settings()
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


def _ocr_request(client: OpenAI, image_bytes: bytes, settings: Any) -> OcrResult:
    """Один запрос к Vision API с изображением. Возвращает распарсенный JSON."""
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    data_uri = f"data:image/png;base64,{b64}"

    response = client.chat.completions.create(
        model=settings.OPENAI_OCR_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": OCR_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": data_uri, "detail": "high"},
                    },
                ],
            }
        ],
        max_tokens=4096,
    )

    if not response.choices:
        raise DictationProcessingError(
            "Не получилось надёжно распознать текст на фото. Отправьте, пожалуйста, более чёткое фото (лист целиком, без бликов)."
        )

    raw = (response.choices[0].message.content or "").strip()
    if raw.startswith("```"):
        lines_raw = raw.split("\n")
        raw = "\n".join(lines_raw[1:-1]) if len(lines_raw) > 2 else raw

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("OCR JSON parse failed: %s", e)
        raise DictationProcessingError(
            "Не удалось разобрать распознанный текст. Попробуйте отправить фото ещё раз."
        ) from e

    lines = data.get("lines") or []
    if not isinstance(lines, list):
        lines = []
    uncertain_spans = data.get("uncertain_spans") or []
    if not isinstance(uncertain_spans, list):
        uncertain_spans = []
    confidence = (data.get("ocr_confidence") or "low").strip().lower()
    if confidence not in ("high", "medium", "low"):
        confidence = "low"

    return {
        "lines": lines,
        "uncertain_spans": uncertain_spans,
        "ocr_confidence": confidence,
    }


def recognize_text_from_image_pass1(image_bytes: bytes) -> OcrResult:
    """Первый проход OCR по предобработанному изображению."""
    client = _get_client()
    settings = get_settings()
    try:
        return _ocr_request(client, image_bytes, settings)
    except DictationProcessingError:
        raise
    except Exception as e:
        logger.exception("OpenAI OCR pass1 failed: %s", e)
        raise OpenAIServiceError(
            "Не удалось связаться с сервисом проверки диктанта. Попробуйте ещё раз чуть позже."
        ) from e


def recognize_text_from_image_pass2(image_bytes: bytes) -> OcrResult:
    """Второй проход OCR по тому же изображению (независимый вызов)."""
    client = _get_client()
    settings = get_settings()
    try:
        return _ocr_request(client, image_bytes, settings)
    except DictationProcessingError:
        raise
    except Exception as e:
        logger.exception("OpenAI OCR pass2 failed: %s", e)
        raise OpenAIServiceError(
            "Не удалось связаться с сервисом проверки диктанта. Попробуйте ещё раз чуть позже."
        ) from e


def ocr_result_to_text(ocr: OcrResult) -> str:
    """Собирает полный текст из результата OCR (lines)."""
    lines = ocr.get("lines") or []
    return "\n".join(str(line) for line in lines)


def check_dictation(recognized_text: str) -> Dict[str, Any]:
    """
    Проверяет диктант по распознанному тексту. Возвращает словарь:
    original_text, corrected_text, spelling_errors, punctuation_errors, notes.
    """
    client = _get_client()
    settings = get_settings()
    user_message = f"Текст диктанта для проверки:\n\n{recognized_text}"

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_CHECK_MODEL,
            messages=[
                {"role": "system", "content": CHECK_DICTATION_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=4096,
        )
    except Exception as e:
        logger.exception("OpenAI check dictation request failed: %s", e)
        raise OpenAIServiceError(
            "Не удалось связаться с сервисом проверки диктанта. Попробуйте ещё раз чуть позже."
        ) from e

    if not response.choices:
        raise DictationProcessingError("Сервис проверки не вернул ответ. Попробуйте ещё раз.")

    raw = (response.choices[0].message.content or "").strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.exception("Failed to parse check dictation JSON: %s", e)
        raise DictationProcessingError(
            "Не удалось разобрать результат проверки. Попробуйте ещё раз."
        ) from e

    result = {
        "original_text": data.get("original_text", recognized_text),
        "corrected_text": data.get("corrected_text", recognized_text),
        "spelling_errors": data.get("spelling_errors") or [],
        "punctuation_errors": data.get("punctuation_errors") or [],
        "notes": data.get("notes") or "",
    }
    if not isinstance(result["spelling_errors"], list):
        result["spelling_errors"] = []
    if not isinstance(result["punctuation_errors"], list):
        result["punctuation_errors"] = []
    return result
