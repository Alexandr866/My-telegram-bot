import os
import openai
import logging
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ключи
openai.api_key = os.environ.get("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет. Я твой дневник. Напиши, как прошёл твой день."
    )

# Ответ на любое сообщение
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = update.effective_user.id
    username = update.effective_user.username or "Без_ника"
    logger.info(f"\u2709\ufe0f От: {username} ({user_id}) — {user_input}")

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
        logger.error(f"\u274c Ошибка OpenAI: {e}")
        await update.message.reply_text("Упс, что-то пошло не так. Попробуй позже.")

# Запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("\u2728 Бот запущен...")
    app.run_polling()
