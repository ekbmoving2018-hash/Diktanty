"""Клиент OpenAI: распознавание текста по фото и проверка диктанта."""

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


def _get_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        settings = get_settings()
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


def recognize_text_from_image(image_bytes: bytes) -> str:
    """
    Отправляет изображение в OpenAI Vision, возвращает буквальную расшифровку текста.
    """
    client = _get_client()
    settings = get_settings()
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    data_uri = f"data:image/jpeg;base64,{b64}"

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_OCR_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": OCR_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            max_tokens=4096,
        )
    except Exception as e:
        logger.exception("OpenAI OCR request failed: %s", e)
        raise OpenAIServiceError("Не удалось связаться с сервисом проверки диктанта. Попробуйте ещё раз чуть позже.") from e

    if not response.choices:
        raise DictationProcessingError("Не получилось надёжно распознать текст на фото. Отправьте, пожалуйста, более чёткое фото (лист целиком, без бликов).")

    text = (response.choices[0].message.content or "").strip()
    if not text:
        raise DictationProcessingError("Не получилось надёжно распознать текст на фото. Отправьте, пожалуйста, более чёткое фото (лист целиком, без бликов).")
    return text


def check_dictation(recognized_text: str) -> Dict[str, Any]:
    """
    Проверяет диктант по распознанному тексту, возвращает словарь с ключами:
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
        raise OpenAIServiceError("Не удалось связаться с сервисом проверки диктанта. Попробуйте ещё раз чуть позже.") from e

    if not response.choices:
        raise DictationProcessingError("Сервис проверки не вернул ответ. Попробуйте ещё раз.")

    raw = (response.choices[0].message.content or "").strip()
    # Убрать возможную обёртку в ```json ... ```
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.exception("Failed to parse check dictation JSON: %s", e)
        raise DictationProcessingError("Не удалось разобрать результат проверки. Попробуйте ещё раз.") from e

    # Нормализация ключей и типов
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
