import logging
import openai
from flask import Flask, request
from telegram import Update, Bot, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.ext import Dispatcher

import os
from collections import defaultdict

# 🔐 КЛЮЧИ (ЗАМЕНИ НА СВОИ или через переменные окружения в Render)
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# 📜 Поддерживаемые языки
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

# 🧠 Контекст на пользователя (хранится в ОЗУ)
user_context = defaultdict(lambda: {"language": "Русский", "messages": []})

# 🔧 Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🌐 Flask app для Render
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put_nowait(update)
    return "ok"

# 🔘 Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [[lang] for lang in LANGUAGES.keys()]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Я твой личный ИИ-дневник. Пожалуйста, выбери язык общения:", reply_markup=markup
    )

# 🌐 Обработка выбора языка
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text
    if lang in LANGUAGES:
        user_context[update.effective_user.id]["language"] = lang
        await update.message.reply_text(f"Язык установлен: {lang}. Можешь начинать писать.")
    else:
        await update.message.reply_text("Выбери язык из списка.")

# 💬 Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_context[user_id]["language"]
    messages = user_context[user_id]["messages"]

    # добавляем новое сообщение в историю
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
        await update.message.reply_text("Упс! Что-то пошло не так. Попробуй позже.")

# 🚀 Запуск приложения
if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_language))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()  # для локального запуска, на Render не используется

