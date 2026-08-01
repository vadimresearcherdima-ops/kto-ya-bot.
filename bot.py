import os
import sys
import asyncio

# --- АВТОМАТИЧЕСКАЯ УСТАНОВКА БИБЛИОТЕКИ ---
try:
    from aiohttp import web
except ImportError:
    import subprocess
    print("Устанавливаю пропущенную библиотеку aiohttp...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
    from aiohttp import web

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# --- 1. НАСТРОЙКА РОБОТА И КЛЮЧЕЙ ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)

# Инструкция для ИИ, кем он должен быть
SYSTEM_PROMPT = "Ты — поддерживающий и мудрый проводник в мир самопознания. Помогай пользователю изучать себя."

# ПРАВИЛЬНЫЙ НАУЧНЫЙ МЕТОД: Передаем инструкцию прямо в настройки модели
MODEL_NAME = 'gemini-1.5-flash'
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=SYSTEM_PROMPT  # Теперь ИИ всегда помнит свою роль без лишних костылей!
)

# --- 2. КАК РОБОТ ОТВЕЧАЕТ В ТЕЛЕГРАМЕ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start при запуске робота"""
    await update.message.reply_text(
        "Привет! Я твой проводник в мир самопознания. О чем бы ты хотел поговорить или что узнать о себе?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений от пользователя"""
    user_text = update.message.text
    
    try:
        # Теперь запускаем чистый чат, так как инструкция уже внутри самой модели
        chat = model.start_chat(history=[])
        
        # Отправляем текст пользователя в Gemini
        response = chat.send_message(user_text)
        
        # Отвечаем пользователю в Телеграм
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("Извини, произошла заминка при обдумывании ответа. Попробуй еще раз чуть позже.")
        print(f"Ошибка при вызове Gemini: {e}")

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
        print("Телеграм-бот успешно запущен...")
        await application.updater.start_polling()
        
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
