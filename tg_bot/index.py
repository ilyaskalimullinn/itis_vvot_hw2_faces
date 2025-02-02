import os
import json
import requests
import random
import binascii
import base64
import shutil


DEFAULT_RESPONSE = {"statusCode": 200, "body": ""}

API_GATEWAY_URL = os.environ.get("API_GATEWAY_URL")
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

    resp = requests.post(url=f"{TELEGRAM_API_URL}/sendMessage", json=reply_message)
    print(resp.content)


def send_face(photo_url, rand_face, message):
    message_id = message["message_id"]
    chat_id = message["chat"]["id"]
    reply_message = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": rand_face,
        "reply_to_message_id": message_id,
    }

    resp = requests.post(url=f"{TELEGRAM_API_URL}/sendPhoto", json=reply_message)
    print(resp.content)


def send_original_photo(photo: str, message):
    photo_bytes = open(f"/function/storage/bucket_photos/{photo}", "rb").read()
    message_id = message["message_id"]
    chat_id = message["chat"]["id"]
    reply_message = {
        "chat_id": chat_id,
        "reply_to_message_id": message_id,
    }

    resp = requests.post(
        url=f"{TELEGRAM_API_URL}/sendPhoto",
        data=reply_message,
        files={
            "photo": photo_bytes,
        },
    )
    print(resp.content)


def create_face_url(face: str) -> str:
    return f"https://{API_GATEWAY_URL}/?face=unknown/{face}"


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
            if rand_face is None:
                send_message("Фотки кончились!", message_in)
                return DEFAULT_RESPONSE
            url = create_face_url(rand_face)
            print(f"Sending photo at {url}")
            send_face(url, rand_face, message_in)
            return DEFAULT_RESPONSE

        if text.startswith("/find "):
            name = text.replace("/find ", "", 1)
            photos = find_face_original_photos(name)

            if len(photos) == 0:
                send_message(f"Фотографии с {name} не найдены")
                return DEFAULT_RESPONSE

            for photo in photos:
                send_original_photo(photo, message_in)
            return DEFAULT_RESPONSE

        if "reply_to_message" in message_in:
            bot_message = message_in["reply_to_message"]
            print(bot_message)

            if "photo" not in bot_message:
                send_message(ERROR_TEXT, message_in)
                return DEFAULT_RESPONSE
            if "caption" not in bot_message:
                send_message(ERROR_TEXT, message_in)
                return DEFAULT_RESPONSE

            caption = bot_message["caption"]

            return save_photo_name(face_photo=caption, name=text, message_in=message_in)

        send_message(ERROR_TEXT, message_in)
        return DEFAULT_RESPONSE

    except Exception as e:
        print(e)
        return DEFAULT_RESPONSE


def save_photo_name(face_photo: str, name: str, message_in: dict) -> dict:
    unknown_faces = os.listdir("/function/storage/bucket_faces/unknown")
    if face_photo not in unknown_faces:
        send_message("Ошибка! Это фото уже пропало", message_in)
        return DEFAULT_RESPONSE

    name_hex = encode_string(name)
    face_dir = f"/function/storage/bucket_faces/known/{name_hex}"
    os.makedirs(face_dir, exist_ok=True)

    shutil.copyfile(
        f"/function/storage/bucket_faces/unknown/{face_photo}",
        f"/function/storage/bucket_faces/known/{name_hex}/{face_photo}",
    )
    os.remove(f"/function/storage/bucket_faces/unknown/{face_photo}")

    send_message(f"Успешо сохранили лицо с именем {name}", message_in)
    return DEFAULT_RESPONSE


def get_random_unknown_face() -> str | None:
    if not os.path.exists("/function/storage/bucket_faces/unknown"):
        return None
    unknown_faces = os.listdir("/function/storage/bucket_faces/unknown")
    if len(unknown_faces) == 0:
        return None
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
