# Diktanty — бот для проверки школьных диктантов по фото

Telegram-бот для учителей русского языка: отправьте фото рукописного диктанта — бот распознает текст, проверит орфографию и пунктуацию и выставит оценку по школьной шкале.

## Возможности

- Распознавание рукописного текста с фото (OCR через OpenAI Vision)
- Проверка орфографии и пунктуации (включая слитное/раздельное написание, запятые)
- Выставление оценки: 0–1 ошибок → 5, 2–3 → 4, 4–6 → 3, 7+ → 2
- Ответ пользователю: распознанный текст, списки ошибок, исправленный текст, статистика и оценка

## Требования

- Python 3.11+
- Токен Telegram-бота ([@BotFather](https://t.me/BotFather))
- Ключ OpenAI API с доступом к vision-моделям

## Установка и запуск

### Локально (для разработки)

1. Клонируйте репозиторий и перейдите в каталог проекта.
2. Создайте виртуальное окружение и установите зависимости:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Скопируйте `.env.example` в `.env` и заполните переменные:

   ```bash
   cp .env.example .env
   ```

   Обязательно укажите:
   - `TELEGRAM_BOT_TOKEN` — токен бота
   - `OPENAI_API_KEY` — ключ OpenAI

4. Запуск через webhook (нужен публичный URL, например [ngrok](https://ngrok.com/)):

   ```bash
   # Укажите в .env:
   # RAILWAY_PUBLIC_URL=https://your-ngrok-url.ngrok.io
   uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

   Затем в Telegram API установите webhook (один раз):

   ```text
   https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your-ngrok-url.ngrok.io/webhook
   ```

   Или с секретом (если задан `WEBHOOK_SECRET`):

   ```text
   https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your-ngrok-url.ngrok.io/webhook/<WEBHOOK_SECRET>
   ```

### Деплой на Railway

1. Создайте проект на [railway.com](https://railway.com) и подключите репозиторий (или загрузите код).
2. В настройках сервиса добавьте переменные окружения (Variables):
   - `TELEGRAM_BOT_TOKEN` — токен от [@BotFather](https://t.me/BotFather)
   - `OPENAI_API_KEY` — ключ OpenAI API  
   - При необходимости: `OPENAI_OCR_MODEL`, `OPENAI_CHECK_MODEL`, `LOG_LEVEL`, `WEBHOOK_SECRET`
3. Включите публичный доступ: **Settings** → **Networking** → **Generate Domain**. Railway задаст переменную `RAILWAY_PUBLIC_DOMAIN` автоматически — бот сам соберёт URL для webhook, отдельно задавать `RAILWAY_PUBLIC_URL` не нужно.
4. Деплой: Railway использует `Procfile` и `runtime.txt` (Python 3.11). При старте приложение вызовет `setWebhook` в Telegram, используя домен из `RAILWAY_PUBLIC_DOMAIN` или `RAILWAY_PUBLIC_URL`.
5. Если webhook не установился, задайте его вручную (подставьте свой домен и токен):
   - Без секрета: `https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<ваш-домен>.up.railway.app/webhook`
   - С секретом: `https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<ваш-домен>.up.railway.app/webhook/<WEBHOOK_SECRET>`
6. Проверка: отправьте боту `/start` или фото диктанта. Логи: **Deployments** → **View Logs**.

## Переменные окружения (.env)

| Переменная | Описание |
|------------|----------|
| `TELEGRAM_BOT_TOKEN` | Токен бота от BotFather (обязательно) |
| `OPENAI_API_KEY` | Ключ OpenAI API (обязательно) |
| `OPENAI_OCR_MODEL` | Модель для распознавания текста с фото (по умолчанию `gpt-4o-mini`) |
| `OPENAI_CHECK_MODEL` | Модель для проверки диктанта (по умолчанию `gpt-4o-mini`) |
| `RAILWAY_PUBLIC_URL` | Публичный URL приложения (опционально; на Railway можно не задавать — используется `RAILWAY_PUBLIC_DOMAIN`) |
| `RAILWAY_PUBLIC_DOMAIN` | Задаётся Railway автоматически при включённом Generate Domain |
| `WEBHOOK_PATH` | Путь для webhook (по умолчанию `webhook`) |
| `WEBHOOK_SECRET` | Секрет в URL webhook (опционально) |
| `LOG_LEVEL` | Уровень логирования: DEBUG, INFO, WARNING, ERROR |

## Структура проекта

- `src/main.py` — точка входа, FastAPI, webhook, глобальный обработчик ошибок
- `src/config/` — настройки из `.env`
- `src/handlers/` — обработчики команд и фото (Telegram)
- `src/services/` — распознавание и проверка диктанта (OpenAI), выставление оценки
- `src/prompts/` — тексты промптов для OCR и проверки
- `src/utils/` — логирование, исключения

## Лицензия

MIT
