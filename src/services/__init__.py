"""Сервисы: OpenAI, проверка диктанта, выставление оценки."""

from src.services.dictation_service import process_dictation_photo
from src.services.grading_service import grade_by_errors

__all__ = ["process_dictation_photo", "grade_by_errors"]
