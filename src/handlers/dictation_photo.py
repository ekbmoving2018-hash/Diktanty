"""Обработчик фото диктанта: скачивание, вызов сервиса, форматирование ответа."""

import asyncio
import html
import logging
from io import BytesIO
from typing import List

from aiogram import Bot, F, Router
from aiogram.types import Message

from src.services.dictation_service import process_dictation_photo
from src.utils.exceptions import DictationProcessingError, OpenAIServiceError

logger = logging.getLogger(__name__)

router = Router(name="dictation_photo")

# Лимит длины одного сообщения Telegram
MAX_MESSAGE_LENGTH = 4096


def _format_errors(errors: list, line_template: str) -> str:
    if not errors:
        return "Нет."
    lines = []
    for i, e in enumerate(errors, 1):
        orig = e.get("original", e.get("original_fragment", "?"))
        corr = e.get("correct", e.get("correct_fragment", "?"))
        expl = e.get("explanation", "")
        lines.append(line_template.format(num=i, orig=orig, corr=corr, expl=expl))
    return "\n".join(lines)


def _chunk_text(text: str, max_len: int = MAX_MESSAGE_LENGTH) -> List[str]:
    if len(text) <= max_len:
        return [text] if text else []
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        chunk = text[:max_len]
        last_newline = chunk.rfind("\n")
        if last_newline > max_len // 2:
            chunk = chunk[: last_newline + 1]
            text = text[last_newline + 1 :]
        else:
            text = text[max_len:]
        chunks.append(chunk)
    return chunks


@router.message(F.photo)
async def handle_dictation_photo(message: Message, bot: Bot) -> None:
    """Скачивает фото максимального размера, запускает проверку диктанта, отправляет результат."""
    user_id = message.from_user.id if message.from_user else 0
    photo = message.photo[-1]
    file_id = photo.file_id
    logger.info("Dictation photo from user_id=%s file_id=%s", user_id, file_id)

    status_msg = await message.answer("Обрабатываю диктант, это может занять до 1 минуты…")

    try:
        file = await bot.get_file(file_id)
        buf = BytesIO()
        await bot.download_file(file.file_path, buf)
        image_bytes = buf.getvalue()
    except Exception as e:
        logger.exception("Failed to download photo: %s", e)
        await status_msg.edit_text("Не удалось скачать фото. Попробуйте отправить ещё раз.")
        return

    try:
        result = await asyncio.to_thread(process_dictation_photo, image_bytes)
    except OpenAIServiceError as e:
        await status_msg.edit_text(str(e))
        return
    except DictationProcessingError as e:
        await status_msg.edit_text(str(e))
        return
    except Exception as e:
        logger.exception("Unexpected error processing dictation: %s", e)
        await status_msg.edit_text("Произошла непредвиденная ошибка. Попробуйте ещё раз позже.")
        return

    await status_msg.delete()

    def esc(s: str) -> str:
        return html.escape(s) if s else ""

    # Блок 1: распознанный текст
    await message.answer(
        "📝 <b>Распознанный текст</b>\n\n" + esc(result.recognized_text[:4000]),
        parse_mode="HTML",
    )

    # Блок 2: орфографические ошибки
    orth_text = _format_errors(
        result.spelling_errors,
        "{num}. «{orig}» → «{corr}». {expl}",
    )
    await message.answer(
        "🔤 <b>Орфографические ошибки</b>\n\n" + esc(orth_text[:4000]),
        parse_mode="HTML",
    )

    # Блок 3: пунктуационные ошибки
    punct_text = _format_errors(
        result.punctuation_errors,
        "{num}. «{orig}» → «{corr}». {expl}",
    )
    await message.answer(
        "📌 <b>Пунктуационные ошибки</b>\n\n" + esc(punct_text[:4000]),
        parse_mode="HTML",
    )

    # Блок 4: исправленный текст (может быть длинным — разбиваем)
    for chunk in _chunk_text(result.corrected_text, max_len=4000):
        await message.answer(
            "✅ <b>Исправленный текст</b>\n\n" + esc(chunk),
            parse_mode="HTML",
        )

    # Блок 5: статистика и оценка
    stats = f"📊 <b>Статистика</b>\n\n{esc(result.stats_message)}"
    if result.notes:
        stats += f"\n\n{esc(result.notes)}"
    await message.answer(stats[:4000], parse_mode="HTML")
