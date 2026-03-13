"""Кастомные исключения для обработки ошибок сервисов."""


class DictationBotError(Exception):
    """Базовое исключение бота."""

    pass


class OpenAIServiceError(DictationBotError):
    """Ошибка при обращении к OpenAI API (сеть, лимиты, ответ)."""

    pass


class DictationProcessingError(DictationBotError):
    """Ошибка при обработке диктанта (парсинг, пустой текст и т.п.)."""

    pass
