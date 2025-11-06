#!/usr/bin/env python3

from __future__ import annotations
import time
from yandex_cloud_ml_sdk import YCloudML
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    folder_id = os.getenv('YANDEX_FOLDER_ID')
    api_key = os.getenv('YANDEX_API_KEY')

    if not folder_id or not api_key:
        raise ValueError("Необходимо указать YANDEX_FOLDER_ID и YANDEX_API_KEY в файле .env")

    user_question = input("Введите ваш вопрос: ")

    messages_1 = [
        {
            "role": "system",
            "text": "Ты — профессиональный умный помощник. Отвечай на вопросы кратко и понятно.",
        },
        {
            "role": "user",
            "text": user_question,
        },
    ]

    sdk = YCloudML(
        folder_id=folder_id,
        auth=api_key,
    )

    model = sdk.models.completions("yandexgpt")

    print("Отправляю запрос к YandexGPT...")

    operation = model.configure(temperature=0.5).run_deferred(messages_1)

    status = operation.get_status()
    while status.is_running:
        time.sleep(5)
        status = operation.get_status()

    result = operation.get_result()
    print("\nОтвет:", result)


if __name__ == "__main__":
    main()
