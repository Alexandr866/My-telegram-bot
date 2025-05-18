import os
import logging
import openai
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import threading

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API-ключи
openai.api_key = os.environ.get("OPENAI_API_KEY")  # <-- из Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")  # <-- из Render

# Flask-приложение
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# Telegram-бот
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет. Я твой дневник. Напиши, как прошёл твой день.")

# Ответ на любые сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = update.effective_user.id
    username = update.effective_user.username or "Без ника"

    logger.info(f"📨 От: {username} (ID: {user_id}) – {user_input}")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты дневниковый ИИ. Не даёшь советов, просто слушаешь и мягко поддерживаешь."},
                {"role": "user", "content": user_input}
            ]
        )
        reply = response["choices"][0]["message"]["content"]
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"❌ Ошибка OpenAI: {e}")
        await update.message.reply_text("Упс, что-то пошло не так. Попробуй позже.")

# Flask-пинг для Render
@app.route('/')
def home():
    return 'OK', 200

# Запуск Telegram-бота в отдельном потоке
def start_bot():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🚀 Бот запускается...")
    application.run_polling()

if __name__ == "__main__":
    threading.Thread(target=start_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
