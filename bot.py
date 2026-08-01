import os
import sys
import asyncio

# --- АВТОМАТИЧЕСКАЯ УСТАНОВКА БИБЛИОТЕКИ (НАША СТРАХОВКА) ---
# Если Render не найдёт библиотеку aiohttp, этот кусочек кода сам её установит
try:
    from aiohttp import web
except ImportError:
    import subprocess
    print("Устанавливаю пропущенную библиотеку aiohttp...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
    from aiohttp import web

# Загружаем остальные нужные инструменты
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# --- 1. НАСТРОЙКА РОБОТА И КЛЮЧЕЙ ---
# Берем секретные ключи, которые вы указали в настройках Render
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Включаем ИИ Gemini
genai.configure(api_key=GEMINI_KEY)

# Инструкция (системный промпт), чтобы робот общался бережно и помогал в самопознании
SYSTEM_PROMPT = "Ты — поддерживающий и мудрый проводник в мир самопознания. Помогай пользователю изучать себя."

# ВАЖНОЕ ОБНОВЛЕНИЕ: Мы поставили самую новую и безотказную модель ИИ!
MODEL_NAME = 'gemini-1.5-flash'
model = genai.GenerativeModel(MODEL_NAME)

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
        # Передаем системную инструкцию первым сообщением в историю, чтобы робот помнил свою роль
        chat = model.start_chat(history=[
            {"role": "user", "parts": [SYSTEM_PROMPT]},
            {"role": "model", "parts": ["Понял тебя. Я готов бережно помогать пользователю в самопознании."]}
        ])
        
        # Отправляем текст пользователя в Gemini
        response = chat.send_message(user_text)
        
        # Отвечаем пользователю в Телеграм
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("Извини, произошла заминка при обдумывании ответа. Попробуй еще раз чуть позже.")
        print(f"Ошибка при вызове Gemini: {e}")

# --- 3. «БУДИЛЬНИК» ДЛЯ СЕРВЕРА RENDER ---
# Этот кусочек кода постоянно отвечает серверу Render, что наш робот не завис
async def handle_render_ping(request):
    return web.Response(text="Робот работает и слушает порт!")

async def start_web_server():
    """Запуск фонового веб-сервера для обмана проверок Render"""
    app = web.Application()
    app.router.add_get('/', handle_render_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Узнаем у Render, какой порт нам открыли. Если порт не задан, используем 8080
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Фоновый веб-сервер успешно запущен на порту {port}")

# --- 4. ГЛАВНЫЙ ЗАПУСК ВСЕЙ ПРОГРАММЫ ---
async def main():
    # 1. Сначала включаем «будильник» для Render, чтобы сервер нас не выключил
    await start_web_server()

    # 2. Настраиваем Телеграм-бота
    application = Application.builder().token(TOKEN).build()

    # 3. Обучаем робота командам и чтению текста
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 4. Запускаем чтение сообщений (Polling) в фоновом режиме
    async with application:
        await application.initialize()
        await application.start()
        print("Телеграм-бот успешно запущен...")
        await application.updater.start_polling()
        
        # Держим программу включенной бесконечно
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    # Запуск главного процесса
    asyncio.run(main())
