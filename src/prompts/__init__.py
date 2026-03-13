"""Промпты для OpenAI (OCR и проверка диктанта)."""

from src.prompts.ocr_prompt import OCR_PROMPT
from src.prompts import check_prompt as _check_prompt

# Поддержка обоих имён константы (CHECK_DICTATION_PROMPT / CHECK_PROMPT)
CHECK_DICTATION_PROMPT = getattr(
    _check_prompt,
    "CHECK_DICTATION_PROMPT",
    getattr(_check_prompt, "CHECK_PROMPT", ""),
)

__all__ = ["OCR_PROMPT", "CHECK_DICTATION_PROMPT"]
