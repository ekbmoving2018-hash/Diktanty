"""Настройки приложения из переменных окружения (.env)."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация из .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    TELEGRAM_BOT_TOKEN: str = Field(..., description="Токен Telegram-бота")
    OPENAI_API_KEY: str = Field(..., description="Ключ OpenAI API")

    OPENAI_OCR_MODEL: str = Field(
        default="gpt-4o-mini",
        description="Модель для распознавания текста с фото (vision)",
    )
    OPENAI_CHECK_MODEL: str = Field(
        default="gpt-4o-mini",
        description="Модель для проверки диктанта",
    )

    RAILWAY_PUBLIC_URL: Optional[str] = Field(
        default=None,
        description="Публичный URL приложения (для webhook). На Railway можно не задавать — подставится из RAILWAY_PUBLIC_DOMAIN.",
    )
    RAILWAY_PUBLIC_DOMAIN: Optional[str] = Field(
        default=None,
        description="Домен сервиса на Railway (автоматически задаётся платформой).",
    )
    WEBHOOK_PATH: str = Field(
        default="webhook",
        description="Путь для приёма апдейтов Telegram",
    )
    WEBHOOK_SECRET: Optional[str] = Field(
        default=None,
        description="Секрет в URL webhook для защиты (если задан, путь будет /webhook/<secret>)",
    )

    LOG_LEVEL: str = Field(default="INFO", description="Уровень логирования")

    def get_public_url(self) -> Optional[str]:
        """Публичный URL приложения для webhook (Railway задаёт RAILWAY_PUBLIC_DOMAIN автоматически)."""
        if self.RAILWAY_PUBLIC_URL:
            return self.RAILWAY_PUBLIC_URL.rstrip("/")
        if self.RAILWAY_PUBLIC_DOMAIN:
            domain = self.RAILWAY_PUBLIC_DOMAIN.strip()
            if not domain.startswith("http"):
                return f"https://{domain}"
            return domain
        return None


@lru_cache
def get_settings() -> Settings:
    """Возвращает загруженные настройки (кэшируются)."""
    return Settings()


settings = get_settings()
