import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Получаем ключи из переменных окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- СИСТЕМНЫЙ ПРОМПТ (ИНСТРУКЦИЯ ДЛЯ НЕЙРОСЕТИ) ---
SYSTEM_PROMPT = """
Ты — диалоговый инструмент философского самопознания. Твоя задача не в том, чтобы дать человеку ответ на вопрос «кто я», а в том, чтобы на каждой встрече помочь ему найти и сформулировать следующий конкретный шаг на его собственном пути — и с течением времени всё меньше быть ему нужным для этого.

Ты не психолог, не терапевт и не духовный учитель, дающий готовые истины. Ты не ставишь диагнозов, не интерпретируешь медицинские факты, не строишь астрологических или эзотерических связей. Твоя работа — задавать точные вопросы, замечать противоречия в словах человека и возвращать их ему в виде следующего вопроса или маленького наблюдения для реальной жизни.

Не отвечай короткой репликой с вопросом в конце. Прежде чем задать следующий вопрос, дай 2–4 содержательных предложения размышления: назови, что именно ты услышал в словах человека, и почему следующий вопрос идёт именно отсюда. Говори конкретно, его же словами, без общих формул поддержки («это очень важно», «я тебя понимаю»). Не задавай больше одного вопроса за раз.
"""

# Настраиваем Gemini API и передаем ей твои правила (системный промпт)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    "gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# Создаем словарь для памяти: бот будет помнить историю переписки с каждым отдельным человеком
user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # При команде /start мы создаем новую чистую историю (чат) для пользователя
    user_chats[user_id] = model.start_chat(history=[])
    
    # Тот самый Блок 0 для первой встречи
    welcome_text = (
        "Здравствуй. Этот инструмент не даст тебе готовых ответов и не определит, «кто ты на самом деле». "
        "Моя задача — задавать точные вопросы, помогать замечать противоречия и находить твой следующий конкретный шаг.\n\n"
        "Единственное, без чего эта работа не имеет смысла, — твоя честность с самим собой. "
        "Обмануть систему или пройти этот путь «на отличку» невозможно, обмануть можно только себя.\n\n"
        "Прежде чем мы начнём, скажи, как к тебе обращаться? И если бы тебе нужно было описать одним словом, "
        "где ты сейчас находишься — начало пути, застревание, кризис, затишье перед шагом или что-то своё, — что ближе всего?"
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text
    
    # Если человек написал не нажав /start, всё равно создаем ему сессию
    if user_id not in user_chats:
         user_chats[user_id] = model.start_chat(history=[])
         
    # Берем конкретную историю переписки именно этого пользователя
    chat = user_chats[user_id]
    
    try:
        # Отправляем сообщение нейросети (с учетом всей прошлой истории)
        response = chat.send_message(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при обращении к ИИ: {e}")

def main():
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("Ошибка: Токены TELEGRAM_TOKEN и GEMINI_API_KEY должны быть заданы!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот успешно запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
