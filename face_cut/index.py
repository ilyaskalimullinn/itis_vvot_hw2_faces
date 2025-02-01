from PIL import Image
import uuid
import json


def handler(event, context):
    print(event)
    all_messages = event["messages"]
    message_body_list = [m["details"]["message"]["body"] for m in all_messages]
    messages = [json.loads(m)["message"] for m in message_body_list]
    for message in messages:
        process_message(message)


def process_message(message: dict):
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

    face_img_path = generate_face_image_path(img_key)

    face.save(face_img_path)
    print(f"Saved image to {face_img_path}")


def generate_face_image_path(original_img_key: str) -> str:
    rand_hex = uuid.uuid4().hex
    image_path = f"/function/storage/bucket_faces/{original_img_key}.{rand_hex}.jpg"
    return image_path
