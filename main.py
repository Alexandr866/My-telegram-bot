import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Список языков и начальные промпты
LANGUAGES = {
    "Русский": "Ты — ИИ-дневник. Помоги пользователю высказаться. Не давай советов, просто слушай и поддерживай.",
    "English": "You are an AI diary. Help the user express themselves. Do not give advice, just listen and support them."
}

# Контекст пользователей
user_context = {}

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[lang] for lang in LANGUAGES]
    await update.message.reply_text(
        "Выбери язык общения:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )

# Установка языка
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text
    if lang in LANGUAGES:
        user_context[update.effective_user.id] = {
            "lang": lang,
            "messages": []
        }
        await update.message.reply_text(f"Язык установлен: {lang}. Можешь начинать писать.")
    else:
        await update.message.reply_text("Выбери язык из предложенных.")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_context:
        await update.message.reply_text("Сначала выбери язык с помощью команды /start.")
        return

    ctx = user_context[user_id]
    ctx["messages"].append({"role": "user", "content": update.message.text})
    ctx["messages"] = ctx["messages"][-20:]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": LANGUAGES[ctx["lang"]]},
                *ctx["messages"]
            ]
        )
        reply = response.choices[0].message.content.strip()
        ctx["messages"].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("Ошибка обработки. Попробуй позже.")

# Запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_language))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

