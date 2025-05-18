import openai
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import threading

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔑 API-ключи
openai.api_key = os.environ.get("OPENAI_API_KEY")  # <-- ВСТАВЬ СВОЙ
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")   # <-- ВСТАВЬ СВОЙ

# Flask
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)
application = Application.builder().token(TELEGRAM_TOKEN).build()

# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет. Я твой дневник. Напиши, как прошёл твой день.")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    logger.info(f"📩 От: {update.effective_user.username} ({update.effective_user.id}) — {user_input}")
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
        logger.error(f"Ошибка OpenAI: {e}")
        await update.message.reply_text("Упс, что-то пошло не так. Попробуй позже.")

# Flask endpoint для проверки
@app.route('/')
def index():
    return "Бот работает!"

# Telegram webhook/polling
@app.route('/start-bot')
def start_bot():
    thread = threading.Thread(target=application.run_polling, name="BotThread")
    thread.start()
    return "Бот запущен."

# Обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
    #fix env vars

