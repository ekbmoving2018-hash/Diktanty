"""Утилиты: логирование, исключения."""

from src.utils.exceptions import (
    DictationBotError,
    DictationProcessingError,
    OpenAIServiceError,
)

__all__ = [
    "DictationBotError",
    "DictationProcessingError",
    "OpenAIServiceError",
]
