"""Обработчики команд /start, /help и прочих сообщений."""

import logging

from aiogram import F, Router
from aiogram.types import Message

logger = logging.getLogger(__name__)

router = Router(name="common")

HELP_TEXT = """Я проверяю школьные диктанты по фото.

Отправьте мне фото рукописного диктанта — я распознаю текст, проверю орфографию и пунктуацию и выставлю оценку по школьной шкале.

Оценки:
• 0–1 ошибок — 5
• 2–3 ошибки — 4
• 4–6 ошибок — 3
• 7+ ошибок — 2

Пришлите одно фото диктанта (не документом, а именно фото)."""


@router.message(F.text, F.text.lower() == "/start")
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Здравствуйте! Я бот для проверки диктантов. Отправьте фото рукописного диктанта.\n\nИспользуйте /help для подсказки."
    )


@router.message(F.text, F.text.lower() == "/help")
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(F.document | F.video | F.audio | F.voice)
async def not_photo_file(message: Message) -> None:
    """Пользователь отправил файл/документ вместо фото."""
    await message.answer(
        "Пожалуйста, пришлите фото рукописного диктанта (не документ/файл). "
        "Используйте /help для подсказки."
    )


@router.message(F.text)
async def not_photo_text(message: Message) -> None:
    """Пользователь отправил текст вместо фото."""
    await message.answer(
        "Пожалуйста, пришлите фото рукописного диктанта. Используйте /help для подсказки."
    )
