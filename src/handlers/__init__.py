"""Обработчики Telegram: команды и фото диктантов."""

from aiogram import Router

from src.handlers import common, dictation_photo


def get_root_router() -> Router:
    """Собирает корневой роутер со всеми хендлерами."""
    router = Router()
    router.include_router(common.router)
    router.include_router(dictation_photo.router)
    return router
