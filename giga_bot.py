#!/usr/bin/env python3

import os
import time
import telebot
import sys
import signal
import logging
from datetime import datetime
from dotenv import load_dotenv
from yandex_cloud_ml_sdk import YCloudML
from gigachat import GigaChat
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Включаем детальное логирование для Yandex SDK
yandex_logger = logging.getLogger('yandex_cloud_ml_sdk')
yandex_logger.setLevel(logging.DEBUG)
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.DEBUG)

# Handler для записи в тот же поток, что и основной логгер
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
yandex_logger.addHandler(handler)
urllib3_logger.addHandler(handler)

# Load environment variables
load_dotenv()

# Get environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
GIGACHAT_CREDENTIALS = os.getenv('GIGACHAT_CREDENTIALS')

# Check if all required environment variables are set
if not all([TELEGRAM_TOKEN, YANDEX_FOLDER_ID, YANDEX_API_KEY, GIGACHAT_CREDENTIALS]):
    raise ValueError("Необходимо указать все переменные окружения в файле .env")

# Initialize Telegram bot with a larger timeout
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)

# Initialize YandexGPT SDK
sdk = YCloudML(
    folder_id=YANDEX_FOLDER_ID,
    auth=YANDEX_API_KEY
)
yandex_model = sdk.models.completions("yandexgpt")

# Initialize GigaChat
giga = GigaChat(
    credentials=GIGACHAT_CREDENTIALS,
    model="GigaChat:latest",
    ca_bundle_file="russian_trusted_root_ca.cer"
)

# User preferences storage
user_preferences = {}

def create_model_selection_keyboard():
    """Create inline keyboard for model selection"""
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("🧙‍♂️ Мудрец GigaChat", callback_data="model_giga"),
        InlineKeyboardButton("🧙‍♀️ Мудрец YandexGPT", callback_data="model_yandex")
    )
    return keyboard

def create_main_keyboard():
    """Create main keyboard with emoji buttons"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton("🔄 Сменить мудреца"))
    keyboard.row(KeyboardButton("ℹ️ Помощь"), KeyboardButton("🎯 Текущий мудрец"))
    return keyboard

def get_yandex_response(user_message: str) -> str:
    """Get response from YandexGPT"""
    logger.info("🧙‍♀️ Запрос к YandexGPT")
    logger.info(f"Текст запроса: {user_message}")
    
    try:
        messages = [
            {
                "role": "system",
                "text": "Ты — мудрый наставник из древних времен. Отвечай на вопросы мудро, с достоинством, иногда используя метафоры.",
            },
            {
                "role": "user",
                "text": user_message,
            },
        ]

        logger.info("Отправка запроса к YandexGPT API...")
        operation = yandex_model.configure(temperature=0.6).run_deferred(messages)

        status = operation.get_status()
        while status.is_running:
            time.sleep(1)
            status = operation.get_status()
            logger.info("Ожидание ответа от YandexGPT...")

        result = operation.get_result()
        
        if result.alternatives:
            response_text = result.alternatives[0].text
            logger.info(f"Ответ получен, длина: {len(response_text)} символов")
            return response_text
        else:
            logger.error("Не удалось получить ответ от YandexGPT")
            return "Извините, не удалось получить ответ."
    except Exception as e:
        logger.error(f"Ошибка при запросе к YandexGPT: {str(e)}")
        return "Извините, произошла ошибка при обработке запроса."

def get_giga_response(user_message: str) -> str:
    """Get response from GigaChat"""
    logger.info("🧙‍♂️ Запрос к GigaChat")
    logger.info(f"Текст запроса: {user_message}")
    
    try:
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "Ты — древний мудрец, обладающий глубокими познаниями. Отвечай на вопросы мудро и с достоинством, используя старославянские обороты речи."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        }
        response = giga.chat(payload=payload)
        
        # Логируем информацию о токенах
        logger.info(f"Использовано токенов: {response.usage.total_tokens}")
        logger.info(f"- Токенов в запросе: {response.usage.prompt_tokens}")
        logger.info(f"- Токенов в ответе: {response.usage.completion_tokens}")
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка в GigaChat response: {str(e)}")
        return "Извините, не удалось получить ответ от GigaChat."

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nПолучен сигнал завершения. Останавливаю бота...")
    bot.stop_polling()
    sys.exit(0)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Handle /start and /help commands"""
    welcome_text = (
        "👋 Приветствую тебя, путник!\n\n"
        "Я — врата к мудрости двух великих оракулов:\n"
        "🧙‍♂️ Мудреца GigaChat и 🧙‍♀️ Мудреца YandexGPT.\n\n"
        "Выбери своего наставника, и да начнется твой путь к познанию!\n\n"
        "Используй кнопки внизу экрана для управления:"
        "\n🔄 Сменить мудреца — выбрать другого наставника"
        "\nℹ️ Помощь — показать это сообщение"
        "\n🎯 Текущий мудрец — узнать, кто сейчас отвечает"
    )
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=create_main_keyboard()
    )
    # Show model selection keyboard
    bot.send_message(
        message.chat.id,
        "Выберите мудреца:",
        reply_markup=create_model_selection_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('model_'))
def handle_model_selection(call):
    """Handle model selection callbacks"""
    chat_id = call.message.chat.id
    model = call.data.split('_')[1]
    user_preferences[chat_id] = model
    
    model_names = {
        'giga': '🧙‍♂️ Мудрец GigaChat',
        'yandex': '🧙‍♀️ Мудрец YandexGPT'
    }
    
    logger.info(f"Пользователь {chat_id} выбрал {model_names[model]}")
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"Вы выбрали {model_names[model]}. Можете задавать свои вопросы!",
        chat_id=chat_id,
        message_id=call.message.message_id
    )

@bot.message_handler(func=lambda message: message.text == "🔄 Сменить мудреца")
def change_model(message):
    """Handle model change request"""
    bot.send_message(
        message.chat.id,
        "Выберите мудреца:",
        reply_markup=create_model_selection_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "ℹ️ Помощь")
def help_command(message):
    """Handle help button"""
    send_welcome(message)

@bot.message_handler(func=lambda message: message.text == "🎯 Текущий мудрец")
def current_model(message):
    """Show current model"""
    chat_id = message.chat.id
    current = user_preferences.get(chat_id, None)
    
    if current == 'giga':
        response = "Сейчас отвечает 🧙‍♂️ Мудрец GigaChat"
    elif current == 'yandex':
        response = "Сейчас отвечает 🧙‍♀️ Мудрец YandexGPT"
    else:
        response = "Мудрец еще не выбран. Используйте кнопку 🔄 Сменить мудреца"
    
    bot.send_message(chat_id, response)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Handle all text messages"""
    chat_id = message.chat.id
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check if model is selected
    if chat_id not in user_preferences:
        bot.send_message(
            chat_id,
            "Пожалуйста, сначала выберите мудреца:",
            reply_markup=create_model_selection_keyboard()
        )
        return
    
    try:
        # Send typing status
        bot.send_chat_action(chat_id, 'typing')
        
        # Log request info
        logger.info(f"Новый запрос от пользователя {chat_id}")
        logger.info(f"Текущий мудрец: {'GigaChat' if user_preferences[chat_id] == 'giga' else 'YandexGPT'}")
        
        # Get response based on selected model
        if user_preferences[chat_id] == 'giga':
            response = get_giga_response(message.text)
            prefix = "🧙‍♂️ Мудрец GigaChat отвечает:\n\n"
        else:  # yandex
            response = get_yandex_response(message.text)
            prefix = "🧙‍♀️ Мудрец YandexGPT отвечает:\n\n"
        
        # Log response info
        logger.info(f"Ответ отправлен пользователю {chat_id}")
        
        # Send response
        bot.send_message(chat_id, prefix + response)
        
    except Exception as e:
        error_message = "Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже."
        bot.send_message(chat_id, error_message)
        logger.error(f"Ошибка при обработке запроса: {str(e)}")

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Бот запущен и готов к работе!")
    try:
        # Start the bot with a larger timeout and non-threaded mode
        # Явно укажем типы апдейтов, чтобы получать callback_query от inline-кнопок
        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=30,
            allowed_updates=["message", "callback_query"]
        )
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        sys.exit(1)
