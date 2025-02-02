import os
import json
import requests
import random
import binascii
import base64


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
            rand_face = get_random_unknown_face()
            send_message(
                f"Вы попросили неотмеченное лицо! Пока без фотки, но вот, что мы бы вам отправили: {rand_face}",
                message_in,
            )
            return DEFAULT_RESPONSE

        if text.startswith("/find "):
            name = text.replace("/find ", "", 1)
            photos = find_face_original_photos(name)
            send_message(
                (
                    f"Вам нужно лицо по имени {name}. Скоро будет! "
                    f"Пока отправляю список названий тех фоток, которые мы бы вам отправили: {photos}"
                ),
                message_in,
            )
            return DEFAULT_RESPONSE

        send_message(ERROR_TEXT, message_in)
        return DEFAULT_RESPONSE

    except Exception as e:
        print(e)
        return DEFAULT_RESPONSE


def get_random_unknown_face() -> str:
    unknown_faces = os.listdir("/function/storage/bucket_faces/unknown")
    return random.choice(unknown_faces)


def find_face_original_photos(name: str) -> list[str]:
    name_hex = encode_string(name)
    os.makedirs("/function/storage/bucket_faces/known", exist_ok=True)
    all_faces = os.listdir("/function/storage/bucket_faces/known")

    if name_hex not in all_faces:
        return []

    known_face_images = os.listdir(f"/function/storage/bucket_faces/known/{name_hex}")
    original_photo_names = [
        convert_known_face_to_original_photo(n) for n in known_face_images
    ]
    return original_photo_names


def convert_known_face_to_original_photo(known_face: str) -> str:
    """
    Convert known face name to original photo name.
    If original photo has name `{original_name}` (including `.jpg` extension),
    known face will be stored in `known/{face_name}/{original_name}.{random_hex}.jpg`

    So this function gets `{original_name}` from `{original_name}.{random_hex}.jpg`

    Args:
        known_face (str): known face key (file name)

    Returns:
        str: original photo key (file name)
    """
    name_split = known_face.split(".jpg")
    original_name = ".jpg".join(name_split[:-2]) + ".jpg"
    return original_name


def encode_string(s: str) -> str:
    return binascii.hexlify(base64.b64encode(s.encode("utf-8"))).decode("utf-8")


def decode_hex(s: str) -> str:
    return base64.b64decode(binascii.unhexlify(s)).decode("utf-8")
