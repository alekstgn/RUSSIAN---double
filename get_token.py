import os
import time
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from gigachat import GigaChat

# Настраиваем запись в файл
with open('token_log.txt', 'w', encoding='utf-8') as log_file:
    def log(message):
        print(message)
        log_file.write(message + '\n')
        log_file.flush()

    log('Старт выполнения get_token.py')

    # Загружаем переменные окружения из файла .env
    load_dotenv()

    # Получаем ключ авторизации из переменной окружения
    credentials = os.getenv('GIGACHAT_CREDENTIALS')
    model = os.getenv('GIGACHAT_MODEL', 'GigaChat:latest')

    log(f"credentials: {credentials}")
    log(f"model: {model}")
    log(f"Файл сертификата существует: {os.path.exists('russian_trusted_root_ca.cer')}")

    log("Создаем экземпляр GigaChat...")
    # Создаем экземпляр GigaChat с указанием пути к корневому сертификату
    giga = GigaChat(credentials=credentials, model=model, ca_bundle_file="russian_trusted_root_ca.cer")
    log("Экземпляр GigaChat создан успешно")

    # Получаем access_token
    try:
        log("Получаем токен...")
        token_info = giga.get_token()
        log("Токен получен, обрабатываем информацию...")
        
        access_token = token_info.access_token
        expires_at = token_info.expires_at

        # Вычисляем секунды до истечения токена
        current_time_ms = int(time.time() * 1000)
        seconds_until_expiry = (expires_at - current_time_ms) // 1000

        # Конвертируем в человеческий вид
        if seconds_until_expiry > 0:
            hours = seconds_until_expiry // 3600
            minutes = (seconds_until_expiry % 3600) // 60
            seconds = seconds_until_expiry % 60

            if hours > 0:
                human_time = f"{hours}ч {minutes}м {seconds}с"
            elif minutes > 0:
                human_time = f"{minutes}м {seconds}с"
            else:
                human_time = f"{seconds}с"
        else:
            human_time = "Токен истек"

        log("=" * 60)
        log("ACCESS TOKEN ПОЛУЧЕН УСПЕШНО!")
        log("=" * 60)
        log(f"Access Token: {access_token}")
        log(f"Секунд до истечения: {seconds_until_expiry}")
        log(f"Время до истечения: {human_time}")
        log("=" * 60)
    except Exception as e:
        log(f"Ошибка при получении access token: {e}")
        log(f"Тип ошибки: {type(e)}")
        import traceback
        log("Полный стек ошибки:")
        log(traceback.format_exc())