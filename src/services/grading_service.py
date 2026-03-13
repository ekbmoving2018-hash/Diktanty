"""Подсчёт ошибок и выставление школьной оценки за диктант."""

from dataclasses import dataclass
from typing import List

# Типы для ошибок из проверки диктанта (совместимы с Pydantic-моделями в dictation_service)
SpellingErrorItem = dict  # {"original", "correct", "explanation"}
PunctuationErrorItem = dict  # {"original_fragment", "correct_fragment", "explanation"}


@dataclass
class GradingResult:
    """Результат оценивания: оценка и текстовая статистика."""

    grade: int  # 2, 3, 4, 5
    spelling_count: int
    punctuation_count: int
    total_errors: int
    stats_message: str


def grade_by_errors(
    spelling_errors: List[SpellingErrorItem],
    punctuation_errors: List[PunctuationErrorItem],
) -> GradingResult:
    """
    Считает ошибки и выставляет оценку по правилам:
    0–1 ошибок → 5; 2–3 → 4; 4–6 → 3; 7+ → 2.
    """
    n_sp = len(spelling_errors)
    n_punct = len(punctuation_errors)
    total = n_sp + n_punct

    if total <= 1:
        grade = 5
    elif total <= 3:
        grade = 4
    elif total <= 6:
        grade = 3
    else:
        grade = 2

    stats_message = (
        f"Орфографические: {n_sp}, пунктуационные: {n_punct}, всего: {total}. Оценка: {grade}"
    )
    return GradingResult(
        grade=grade,
        spelling_count=n_sp,
        punctuation_count=n_punct,
        total_errors=total,
        stats_message=stats_message,
    )
