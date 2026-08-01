import os
import sys
import asyncio

# --- АВТОМАТИЧЕСКАЯ УСТАНОВКА НОВЫХ БИБЛИОТЕК GOOGLE И ТЕЛЕГРАМА ---
# Этот блок сам скачает новейший пакет google-genai прямо на сервере Render
try:
    from aiohttp import web
    from google import genai
except ImportError:
    import subprocess
    print("Устанавливаю новейшие библиотеки ИИ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp", "google-genai", "python-telegram-bot==21.10"])
    from aiohttp import web
    from google import genai

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. НАСТРОЙКА КЛЮЧЕЙ И КЛИЕНТА GOOGLE ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Запускаем новый, современный клиент ИИ по правилам Google
ai_client = genai.Client(api_key=GEMINI_KEY)

# Инструкция для ИИ, кем он должен быть
SYSTEM_PROMPT = "Ты — поддерживающий и мудрый проводник в мир самопознания. Помогай пользователю изучать себя."
MODEL_NAME = 'gemini-2.5-flash'  # Используем самую свежую и быструю модель

# --- 2. КАК РОБОТ ОТВЕЧАЕТ В ТЕЛЕГРАМЕ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start при запуске робота"""
    await update.message.reply_text(
        "Привет! Я твой проводник в мир самопознания. О чем бы ты хотел поговорить или что узнать о себе?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений от пользователя через новый ИИ"""
    user_text = update.message.text
    
    try:
        # Вызываем новый ИИ по современным правилам
        response = ai_client.models.generate_content(
            model=MODEL_NAME,
            contents=user_text,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT
            )
        )
        # Отвечаем пользователю в Телеграм
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("Извини, произошла заминка при обдумывании ответа. Попробуй еще раз чуть позже.")
        print(f"Ошибка нового Gemini: {e}")

# --- 3. «БУДИЛЬНИК» ДЛЯ СЕРВЕРА RENDER ---
async def handle_render_ping(request):
    return web.Response(text="Робот работает и слушает порт!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_render_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Фоновый веб-сервер успешно запущен на порту {port}")

# --- 4. ГЛАВНЫЙ ЗАПУСК ВСЕЙ ПРОГРАММЫ ---
async def main():
    await start_web_server()

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    async with application:
        await application.initialize()
        await application.start()
        print("Телеграм-бот успешно запущен на новой библиотеке...")
        await application.updater.start_polling()
        
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
