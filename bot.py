import os
import asyncio
from telegram import Update, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, PreCheckoutQueryHandler, filters, ContextTypes
import google.generativeai as genai

# Ключи из переменных окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- СИСТЕМНЫЙ ПРОМПТ ---
SYSTEM_PROMPT = """
Ты — диалоговый инструмент философского самопознания. Твоя задача не в том, чтобы дать человеку ответ на вопрос «кто я», а в том, чтобы на каждой встрече помочь ему найти и сформулировать следующий конкретный шаг на его собственном пути — и с течением времени всё меньше быть ему нужным для этого.

Ты не психолог, не терапевт и не духовный учитель, дающий готовые истины. Ты не ставишь диагнозов, не интерпретируешь медицинские факты, не строишь астрологических или эзотерических связей. Твоя работа — задавать точные вопросы, замечать противоречия в словах человека и возвращать их ему в виде следующего вопроса или маленького наблюдения для реальной жизни.

Не отвечай короткой репликой с вопросом в конце. Прежде чем задать следующий вопрос, дай 2–4 содержательных предложения размышления: назови, что именно ты услышал в словах человека, и почему следующий вопрос идёт именно отсюда. Говори конкретно, его же словами, без общих формул поддержки («это очень важно», «я тебя понимаю»). Не задавай больше одного вопроса за раз.
"""

# Устанавливаем безотказную базовую модель
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# --- ПАМЯТЬ И СТАТИСТИКА ---
user_chats = {}
user_stats = {} # Здесь храним {"sessions": 0, "messages": 0, "paid": False}

# Фокус: передаем правила нейросети как первое сообщение в истории!
INITIAL_HISTORY = [
    {"role": "user", "parts": [SYSTEM_PROMPT]},
    {"role": "model", "parts": ["Я понял свои инструкции. Я готов задавать точные вопросы и вести философский диалог."]}
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    # Запускаем чат, сразу вкладывая в него историю с правилами
    user_chats[user_id] = model.start_chat(history=INITIAL_HISTORY.copy())
    user_stats[user_id] = {"sessions": 0, "messages": 0, "paid": False}
    
    welcome_text = (
        "Здравствуй. Этот инструмент не даст тебе готовых ответов и не определит, «кто ты на самом деле».\n\n"
        "Первые 2 сессии (по 15 сообщений) — бесплатны. Далее 1 сессия стоит $4.\n\n"
        "Прежде чем мы начнём, скажи, как к тебе обращаться? И опиши одним словом, где ты сейчас находишься — начало пути, застревание, кризис?"
    )
    await update.message.reply_text(welcome_text)

# --- ФУНКЦИЯ ОПЛАТЫ ---
async def send_payment_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    
    title = "Новая сессия самопознания"
    description = "Оплата следующей сессии (15 сообщений)."
    payload = "session_payment"
    currency = "XTR" 
    price = 200 
    prices = [LabeledPrice("Сессия", price)]

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Оплатить Картой / PayPal ($4)", url="https://lemon-squeezy.com/ваша-ссылка")]
    ])

    await context.bot.send_invoice(
        chat_id, title, description, payload,
        provider_token="", 
        currency=currency, prices=prices,
        reply_markup=keyboard
    )

# --- ОБРАБОТКА УСПЕШНОЙ ОПЛАТЫ ---
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_stats:
        user_stats[user_id]["paid"] = True
        user_stats[user_id]["messages"] = 0
    await update.message.reply_text("Оплата успешно получена! Можем продолжать. Напиши свой ответ, чтобы продолжить диалог.")

# --- ОСНОВНАЯ ЛОГИКА ДИАЛОГА ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text
    
    if user_id not in user_stats:
        user_stats[user_id] = {"sessions": 0, "messages": 0, "paid": False}
    if user_id not in user_chats:
         user_chats[user_id] = model.start_chat(history=INITIAL_HISTORY.copy())
         
    stats = user_stats[user_id]
    
    # ПРОВЕРКА ЛИМИТОВ
    if stats["messages"] >= 15:
        stats["sessions"] += 1
        stats["messages"] = 0
        stats["paid"] = False 
        await update.message.reply_text("Твоя сессия из 15 сообщений подошла к концу.")
        
    if stats["sessions"] >= 2 and not stats["paid"]:
        await send_payment_options(update, context)
        return 
    
    # ЕСЛИ ВСЁ ОК — ОБЩАЕМСЯ С НЕЙРОСЕТЬЮ
    chat = user_chats[user_id]
    try:
        stats["messages"] += 1 
        response = chat.send_message(user_text)
        messages_left = 15 - stats["messages"]
        await update.message.reply_text(f"{response.text}\n\n*(Осталось сообщений в сессии: {messages_left})*", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при обращении к ИИ: {e}")

def main():
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("Ошибка: Токены TELEGRAM_TOKEN и GEMINI_API_KEY должны быть заданы!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот успешно запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
