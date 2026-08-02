import telebot
import requests
import json
import os

# --- НАСТРОЙКИ ---
# Токен Telegram бот берет из настроек Render (Environment Variables)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ключ DeepSeek берет из настроек Render (Environment Variables)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Создаем объект бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Адрес API DeepSeek
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

# --- ФУНКЦИЯ ОБРАЩЕНИЯ К DEEPSEEK ---
def get_deepseek_response(user_message):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ты полезный и вежливый ассистент."},
            {"role": "user", "content": user_message}
        ],
        "stream": False
    }

    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"Ошибка при запросе к DeepSeek: {e}")
        return "Извините, произошла ошибка при обращении к нейросети."

# --- ОБРАБОТЧИК КОМАНДЫ /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот, подключенный к DeepSeek. Напиши мне что-нибудь.")

# --- ОБРАБОТЧИК ЛЮБОГО ТЕКСТОВОГО СООБЩЕНИЯ ---
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.send_chat_action(message.chat.id, 'typing')
    ai_response = get_deepseek_response(message.text)
    bot.reply_to(message, ai_response)

# --- ЗАПУСК БОТА ---
if __name__ == "__main__":
    print("Бот запущен и слушает сообщения...")
    bot.infinity_polling()
