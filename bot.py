import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# 1. ПОЛУЧЕНИЕ НАСТРОЕК С СЕРВЕРА RENDER
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Включаем ИИ от Google
genai.configure(api_key=GEMINI_KEY)

# Инструкция для ИИ
SYSTEM_PROMPT = "Ты — поддерживающий и мудрый проводник в мир самопознания. Помогай пользователю изучать себя."

# 2. ЛОГИКА ОТВЕТА В ТЕЛЕГРАМЕ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "Привет! Я твой проводник в мир самопознания. О чем бы ты хотел поговорить?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений пользователя"""
    user_text = update.message.text
    
    try:
        # Железобетонный, самый стабильный метод вызова Gemini 1.5, который точно работает
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=SYSTEM_PROMPT
        )
        
        response = model.generate_content(user_text)
        
        if response.text:
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("ИИ вернул пустой ответ. Попробуйте еще раз.")
            
    except Exception as e:
        print(f"ОШИБКА GEMINI: {e}")
        await update.message.reply_text("Извини, произошла заминка при обдумывании ответа.")

# 3. ОБЯЗАТЕЛЬНЫЙ «БУДИЛЬНИК» ДЛЯ RENDER (ВЕБ-СЕРВЕР)
async def handle_render_ping(request):
    return web.Response(text="Бот онлайн")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_render_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# 4. ГЛАВНЫЙ ЗАПУСК
async def main():
    # Запускаем фоновый порт для Render
    await start_web_server()

    # Настраиваем Телеграм-бота
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
