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
    top, left, right, bottom = (
        message["top"],
        message["left"],
        message["right"],
        message["bottom"],
    )
    img_path = f"/function/storage/bucket_photos/{img_key}"
    img = Image.open(img_path)

    face = img.crop((left, top, left + right, top + bottom))

    face_img_path = generate_face_image_path(img_path)

    face.save(face_img_path)
    print(f"Saved image to {face_img_path}")


def generate_face_image_path(original_img_path: str) -> str:
    rand_hex = uuid.uuid4().hex
    image_path = f"{original_img_path}.{rand_hex}.jpeg"
    return image_path
