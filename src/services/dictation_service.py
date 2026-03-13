"""Бизнес-логика: предобработка фото, OCR (два прохода), валидация, проверка диктанта, оценка."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from src.services.grading_service import grade_by_errors
from src.services.image_preprocess import preprocess_handwritten_image
from src.services.openai_client import (
    check_dictation,
    ocr_result_to_text,
    recognize_text_from_image_pass1,
    recognize_text_from_image_pass2,
)
from src.services.ocr_validation import validate_ocr_result
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
    1) Предобработка изображения
    2) Два независимых прохода OCR по обработанному изображению
    3) Валидация: confidence, кол-во неразборчивого, сходство проходов
    4) При успехе — проверка диктанта и выставление оценки
    """
    processed = preprocess_handwritten_image(image_bytes)
    logger.info("Image preprocessed, size=%d bytes", len(processed))

    ocr1 = recognize_text_from_image_pass1(processed)
    ocr2 = recognize_text_from_image_pass2(processed)

    is_valid, error_message = validate_ocr_result(ocr1, ocr2)
    if not is_valid:
        raise DictationProcessingError(error_message)

    recognized_text = ocr_result_to_text(ocr1)
    logger.info("OCR validated, text length=%d", len(recognized_text))

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
