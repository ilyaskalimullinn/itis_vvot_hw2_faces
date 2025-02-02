from PIL import Image
import uuid
import json
import os
import io
import boto3


ACCESS_KEY = os.environ.get("ACCESS_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
BUCKET_FACES = os.environ.get("BUCKET_FACES")


def handler(event, context):
    print(event)
    client = boto3.client(
        "s3",
        endpoint_url="https://storage.yandexcloud.net/",
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )
    all_messages = event["messages"]
    message_body_list = [m["details"]["message"]["body"] for m in all_messages]
    messages = [json.loads(m)["message"] for m in message_body_list]
    for message in messages:
        process_message(message, client)


def process_message(message: dict, client):
    img_key = message["image_key"]
    x, y, w, h = (
        message["x"],
        message["y"],
        message["w"],
        message["h"],
    )
    img_path = f"/function/storage/bucket_photos/{img_key}"
    img = Image.open(img_path)

    face = img.crop((x, y, x + w, y + h))

    face_img_key = generate_face_image_key(img_key)

    face_byte_io = io.BytesIO()
    face.save(face_byte_io, format="JPEG")

    client.upload_fileobj(
        Fileobj=io.BytesIO(face_byte_io.getvalue()),
        Bucket=BUCKET_FACES,
        Key=face_img_key,
        ExtraArgs={"ContentType": "image/jpeg"},
        Callback=None,
        Config=None,
    )


def generate_face_image_key(original_img_key: str) -> str:
    rand_hex = uuid.uuid4().hex
    image_path = f"unknown/{original_img_key}.{rand_hex}.jpg"
    return image_path
