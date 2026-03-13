"""Бизнес-логика: распознавание фото диктанта, проверка, оценка, агрегация результата."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from src.services.openai_client import check_dictation, recognize_text_from_image
from src.services.grading_service import grade_by_errors
from src.utils.exceptions import DictationProcessingError, OpenAIServiceError

logger = logging.getLogger(__name__)


@dataclass
class DictationResult:
    """Итоговый результат обработки диктанта для отправки пользователю."""

    recognized_text: str
    original_text: str
    corrected_text: str
    spelling_errors: List[Dict[str, Any]]
    punctuation_errors: List[Dict[str, Any]]
    notes: str
    grade: int
    spelling_count: int
    punctuation_count: int
    total_errors: int
    stats_message: str


def process_dictation_photo(image_bytes: bytes) -> DictationResult:
    """
    1) OCR по фото → распознанный текст
    2) Проверка диктанта → JSON с ошибками и исправленным текстом
    3) Подсчёт ошибок и оценка
    Возвращает DictationResult для форматирования в хендлере.
    """
    recognized_text = recognize_text_from_image(image_bytes)
    logger.info("OCR completed, text length=%d", len(recognized_text))

    check = check_dictation(recognized_text)
    grading = grade_by_errors(
        check["spelling_errors"],
        check["punctuation_errors"],
    )

    return DictationResult(
        recognized_text=recognized_text,
        original_text=check["original_text"],
        corrected_text=check["corrected_text"],
        spelling_errors=check["spelling_errors"],
        punctuation_errors=check["punctuation_errors"],
        notes=check["notes"],
        grade=grading.grade,
        spelling_count=grading.spelling_count,
        punctuation_count=grading.punctuation_count,
        total_errors=grading.total_errors,
        stats_message=grading.stats_message,
    )
