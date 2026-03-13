"""Валидация результата OCR перед переходом к проверке диктанта."""

import difflib
import logging
from typing import Any, Dict, Tuple

from src.services.openai_client import ocr_result_to_text

logger = logging.getLogger(__name__)

UNREADABLE_MARKER = "[[неразборчиво]]"

# Минимальное сходство двух проходов OCR (0..1), иначе считаем ненадёжным
MIN_PASS_SIMILARITY = 0.82

# Доля строк с [[неразборчиво]] или доля символов — выше порога = не переходить к проверке
MAX_UNREADABLE_LINE_RATIO = 0.35  # если больше 35% строк содержат маркер
MAX_UNREADABLE_CHAR_RATIO = 0.15  # или больше 15% символов — маркер (грубая оценка)


def _count_unreadable(text: str) -> Tuple[int, int]:
    """Возвращает (число вхождений маркера, общая длина текста)."""
    return text.count(UNREADABLE_MARKER), len(text)


def _line_count_with_marker(lines: list) -> int:
    """Число строк, в которых встречается маркер неразборчиво."""
    return sum(1 for line in (lines or []) if UNREADABLE_MARKER in str(line))


def validate_ocr_result(
    ocr_pass1: Dict[str, Any],
    ocr_pass2: Dict[str, Any],
) -> Tuple[bool, str]:
    """
    Проверяет, можно ли переходить к этапу проверки диктанта.
    Возвращает (is_valid, error_message).
    Если is_valid False, error_message — сообщение для пользователя.
    """
    confidence = (ocr_pass1.get("ocr_confidence") or "low").strip().lower()
    if confidence == "low":
        return (
            False,
            "Распознавание текста получилось ненадёжным (низкая уверенность). Отправьте более чёткое фото диктанта.",
        )

    lines1 = ocr_pass1.get("lines") or []
    lines2 = ocr_pass2.get("lines") or []
    if not lines1 and not lines2:
        return (
            False,
            "Не удалось распознать текст на фото. Отправьте чёткое фото рукописного диктанта.",
        )

    text1 = ocr_result_to_text(ocr_pass1)
    text2 = ocr_result_to_text(ocr_pass2)
    similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
    if similarity < MIN_PASS_SIMILARITY:
        logger.info("OCR pass similarity too low: %.2f", similarity)
        return (
            False,
            "Два прохода распознавания сильно различаются — качество фото недостаточное. Сделайте более чёткий снимок листа целиком.",
        )

    # Слишком много неразборчивого
    line_count = max(len(lines1), len(lines2), 1)
    lines_with_marker = max(_line_count_with_marker(lines1), _line_count_with_marker(lines2))
    if lines_with_marker / line_count > MAX_UNREADABLE_LINE_RATIO:
        return (
            False,
            "Слишком много неразборчивых фрагментов. Отправьте более чёткое фото (хорошее освещение, лист целиком).",
        )

    unread_count, total_len = _count_unreadable(text1)
    if total_len > 0 and (unread_count * len(UNREADABLE_MARKER) / total_len) > MAX_UNREADABLE_CHAR_RATIO:
        return (
            False,
            "Слишком много неразборчивых участков в тексте. Отправьте более чёткое фото.",
        )

    return True, ""
