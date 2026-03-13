"""Точка входа: FastAPI, Telegram Bot, webhook для Railway."""

import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.handlers import get_root_router
from src.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()
bot = Bot(
    token=settings.TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()
dp.include_router(get_root_router())


@dp.error()
async def global_error_handler(event: ErrorEvent) -> None:
    """Отправляет пользователю сообщение при любой необработанной ошибке."""
    logger.exception("Unhandled error: %s", event.exception)
    update = event.update
    chat_id = None
    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query and update.callback_query.message:
        chat_id = update.callback_query.message.chat.id
    elif update.edited_message:
        chat_id = update.edited_message.chat.id
    if chat_id is not None:
        try:
            await bot.send_message(
                chat_id,
                "Произошла непредвиденная ошибка. Попробуйте ещё раз позже.",
            )
        except Exception as send_err:
            logger.exception("Failed to send error message to user: %s", send_err)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Установка и снятие webhook при старте/остановке."""
    base_url = settings.get_public_url()
    if base_url:
        path = settings.WEBHOOK_PATH.strip("/") or "webhook"
        if settings.WEBHOOK_SECRET:
            path = f"{path}/{settings.WEBHOOK_SECRET}"
        url = f"{base_url}/{path}"
        await bot.set_webhook(url)
        logger.info("Webhook set: %s", url)
    yield
    await bot.session.close()


app = FastAPI(title="Diktanty Bot", lifespan=lifespan)


_WEBHOOK_PATH = settings.WEBHOOK_PATH.strip("/") or "webhook"


async def _handle_webhook(request: Request, secret: str) -> Response:
    if settings.WEBHOOK_SECRET and secret != settings.WEBHOOK_SECRET:
        return Response(status_code=403)
    try:
        body = await request.json()
        await dp.feed_webhook_update(bot, body)
        return JSONResponse(content={"ok": True})
    except Exception as e:
        logger.exception("Webhook error: %s", e)
        return JSONResponse(content={"ok": False}, status_code=500)


@app.post(f"/{_WEBHOOK_PATH}")
async def webhook_no_secret(request: Request) -> Response:
    """Принимает апдейты: POST /webhook."""
    return await _handle_webhook(request, "")


@app.post(f"/{_WEBHOOK_PATH}/{{secret:path}}")
async def webhook_with_secret(request: Request, secret: str) -> Response:
    """Принимает апдейты: POST /webhook/<WEBHOOK_SECRET>."""
    return await _handle_webhook(request, secret)


@app.get("/health")
async def health() -> dict:
    """Проверка живости для Railway."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000)
