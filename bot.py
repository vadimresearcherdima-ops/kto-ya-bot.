import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# 1. НАСТРОЙКА КЛЮЧЕЙ И НАУЧНОЙ МОДЕЛИ GEMINI
# Берем секретные ключи, которые вы указали в настройках Render
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)

# Инструкция для робота (системный промпт), чтобы он помогал в самопознании
SYSTEM_PROMPT = "Ты — поддерживающий и мудрый проводник в мир самопознания. Помогай пользователю изучать себя."

# Настраиваем модель Gemini. Используем надежную gemini-pro
model = genai.GenerativeModel('gemini-pro')

# 2. ЛОГИКА РАБОТЫ РОБОТА (ОБРАБОТКА СООБЩЕНИЙ)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start при запуске робота"""
    await update.message.reply_text(
        "Привет! Я твой проводник в мир самопознания. О чем бы ты хотел поговорить или что узнать о себе?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений от пользователя"""
    user_text = update.message.text
    
    try:
        # Создаем диалог и передаем системную инструкцию первым сообщением в историю
        chat = model.start_chat(history=[
            {"role": "user", "parts": [SYSTEM_PROMPT]},
            {"role": "model", "parts": ["Понял тебя. Я готов помогать пользователю в самопознании."]}
        ])
        
        # Отправляем текст пользователя в Gemini
        response = chat.send_message(user_text)
        
        # Отвечаем пользователю в Телеграм
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("Извини, произошла заминка при общении с ИИ. Попробуй еще раз чуть позже.")
        print(f"Ошибка Gemini: {e}")

# 3. ВЕБ-ЗАГЛУШКА ДЛЯ ПЛАТФОРМЫ RENDER
# Этот кусочек кода отвечает серверу Render, что наш робот работает и все хорошо
async def handle_render_ping(request):
    return web.Response(text="Робот работает и слушает порт!")

async def start_web_server():
    """Запуск фонового веб-сервера для обмана проверок Render"""
    app = web.Application()
    # Когда Render стучится по главному адресу, мы отвечаем ему текстом
    app.router.add_get('/', handle_render_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render автоматически передает номер порта в переменную PORT. Если её нет, ставим 8080
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Фоновый веб-сервер успешно запущен на порту {port}")

# 4. ГЛАВНЫЙ ЗАПУСК ВСЕЙ ПРОГРАММЫ
async def main():
    # Сначала запускаем наш «будильник» для Render
    await start_web_server()

    # Настраиваем Телеграм-бота
    application = Application.builder().token(TOKEN).build()

    # Обучаем командам и тексту
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем чтение сообщений (Polling) так, чтобы оно не мешало веб-серверу
    async with application:
        await application.initialize()
        await application.start()
        print("Телеграм-бот успешно запущен через polling...")
        await application.updater.start_polling()
        
        # Держим программу запущенной бесконечно
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    # Запускаем главный асинхронный процесс
    asyncio.run(main())
