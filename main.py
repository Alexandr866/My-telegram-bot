import logging
import os
from collections import defaultdict

import openai
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# 🔐 Ключи из переменных окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# 🌍 Поддерживаемые языки
LANGUAGES = {
    "Русский": "Ты — ИИ-дневник. Помоги пользователю высказаться. Не давай советов, не перебивай, просто слушай и поддерживай.",
    "English": "You are an AI diary. Help the user express themselves. Do not give advice, just listen and support them.",
    "Қазақша": "Сен – жасанды интеллект күнделік. Тек тыңда, кеңес берме.",
    "Deutsch": "Du bist ein KI-Tagebuch. Höre zu und unterstütze.",
    "Українська": "Ти — ІІ-щоденник. Не давай порад, просто слухай і підтримуй.",
    "Português": "Você é um diário de IA. Apenas escute e apoie.",
    "Español": "Eres un diario de IA. Escucha y apoya sin dar consejos.",
    "Français": "Tu es un journal IA. Écoute et soutiens sans juger.",
}

# 🧠 Память на пользователя (RAM)
user_context = defaultdict(lambda: {"language": "Русский", "messages": []})

# 🔧 Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Команда /start — выбор языка
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [[lang] for lang in LANGUAGES]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Я твой личный ИИ-дневник. Пожалуйста, выбери язык общения:", reply_markup=markup
    )

# Установка языка
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text.strip()
    if lang in LANGUAGES:
        user_context[update.effective_user.id]["language"] = lang
        await update.message.reply_text(f"Язык установлен: {lang}. Можешь писать.")
    else:
        await handle_message(update, context)  # если это не язык — обрабатываем как обычное сообщение

# Генерация ответа через OpenAI
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = user_context[user_id]
    lang = user_data["language"]
    messages = user_data["messages"]

    messages.append({"role": "user", "content": update.message.text})
    if len(messages) > 20:
        messages = messages[-20:]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": LANGUAGES[lang]},
                *messages
            ]
        )
        reply = response.choices[0].message.content.strip()
        messages.append({"role": "assistant", "content": reply})
        user_context[user_id]["messages"] = messages
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        await update.message.reply_text("Что-то пошло не так. Попробуй позже.")

# 🚀 Запуск polling (для Render — Background Worker)
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_language))
    app.run_polling()

