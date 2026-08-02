
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# ===== НАСТРОЙКИ =====
logging.basicConfig(level=logging.INFO)

# === ПРОВЕРКА КЛЮЧЕЙ ===
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("❌ Не найден DEEPSEEK_API_KEY. Добавь его в Render!")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("❌ Не найден TELEGRAM_BOT_TOKEN. Добавь его в Render!")

# === СОЗДАЁМ КЛИЕНТА ДЛЯ DEEPSEEK ===
client = OpenAI(
    api_key=DEEPSEEK_API_KEY=api_key = " sk-dd6e4d8284404ae29ed994c823cb07dd"         
    base_url="https://api.deepseek.com"
)

# === ЛИЧНОСТЬ БОТА (СИСТЕМНЫЙ ПРОМПТ) ===
SYSTEM_PROMPT = (
    "Ты — поддерживающий и мудрый проводник в мир самопознания. "
    "Помогай пользователю изучать себя. Отвечай тепло, но не навязчиво. "
    "Задавай наводящие вопросы, если чувствуешь, что человек хочет глубже разобраться."
)

# === ФУНКЦИЯ ЗАПРОСА К DEEPSEEK ===
async def get_deepseek_response(user_message: str) -> str:
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Ошибка DeepSeek: {e}")
        return "⚠️ Произошла ошибка. Попробуй позже."

# === КОМАНДА /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌟 Привет! Я — твой проводник в самопознание.\n"
        "Задавай мне любые вопросы о себе, мыслях, чувствах — будем разбираться вместе."
    )

# === ОБРАБОТКА СООБЩЕНИЙ ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text("🧠 Думаю... пишу...")

    bot_reply = await get_deepseek_response(user_text)

    if len(bot_reply) > 4096:
        for chunk in bot_reply.split("\n\n"):
            await update.message.reply_text(chunk)
    else:
        await update.message.reply_text(bot_reply)

# === ЗАПУСК ===
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    port = int(os.environ.get("PORT", 10000))
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/"
    )

if __name__ == "__main__":
    main()
