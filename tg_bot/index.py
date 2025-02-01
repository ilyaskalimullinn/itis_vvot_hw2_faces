import os
import json
import requests


DEFAULT_RESPONSE = {"statusCode": 200, "body": ""}
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

HELP_TEXT = """Я бот по нахождению и разметке лиц.
Напишите `/getface` — я пришлю вам лицо человека, у которого еще не отмечено имя.
Напишите `/find {name}` — я найду вам лицо человека по имени"""

ERROR_TEXT = "Ошибка"


def send_message(text, message):
    """Отправка сообщения пользователю Telegram."""
    message_id = message["message_id"]
    chat_id = message["chat"]["id"]
    reply_message = {
        "chat_id": chat_id,
        "text": text,
        "reply_to_message_id": message_id,
    }

    requests.post(url=f"{TELEGRAM_API_URL}/sendMessage", json=reply_message)


def handler(event, context):
    """Обработчик облачной функции. Реализует Webhook для Telegram Bot."""

    # Logging
    print(event)
    try:
        if TELEGRAM_BOT_TOKEN is None:
            return DEFAULT_RESPONSE

        update = json.loads(event["body"])

        if "message" not in update:
            return DEFAULT_RESPONSE

        message_in = update["message"]

        if "text" not in message_in:
            send_message(ERROR_TEXT, message_in)
            return DEFAULT_RESPONSE

        text: str = message_in["text"]

        if text == "/help" or text == "/start":
            send_message(HELP_TEXT, message_in)
            return DEFAULT_RESPONSE

        if text == "/getface":
            send_message(
                "Вы попросили неотмеченное лицо! Пока это не реализовано, но скоро будет!",
                message_in,
            )
            return DEFAULT_RESPONSE

        if text.startswith("/find "):
            name = text.replace("/find ", "", 1)
            send_message(f"Вам нужно лицо по имени {name}. Скоро будет!", message_in)
            return DEFAULT_RESPONSE

        send_message(ERROR_TEXT, message_in)
        return DEFAULT_RESPONSE

    except:
        return DEFAULT_RESPONSE
