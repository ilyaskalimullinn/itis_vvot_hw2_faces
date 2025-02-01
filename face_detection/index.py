import cv2
import boto3
import os
import json
import base64


QUEUE_URL = os.environ.get("QUEUE_URL")
ACCESS_KEY = os.environ.get("ACCESS_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")

auth_string = f"{ACCESS_KEY}:{SECRET_KEY}"
auth_string_encoded = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    # "Authorization": f"Basic {auth_string_encoded}",
}


def handler(event, context):
    print(event)
    print(context)
    messages = event["messages"]
    messages_to_queue = []
    for message in messages:
        object_id = message["details"]["object_id"]
        img_path = f"/function/storage/bucket_photos/{object_id}"
        faces = find_faces(img_path)

        for face in faces:
            top, right, bottom, left = face.tolist()
            message_to_queue = {
                "image_key": object_id,
                "top": top,
                "right": right,
                "bottom": bottom,
                "left": left,
            }
            messages_to_queue.append(message_to_queue)

    print(messages_to_queue)
    send_messages_to_queue(messages_to_queue)
    return {"statusCode": 200, "body": ""}


def find_faces(img_path):
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    img = cv2.imread(img_path)
    # Convert the image to grayscale (required by the classifier)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    faces = [faces[i, :] for i in range(faces.shape[0])]
    return faces


def send_messages_to_queue(messages: list):
    client = boto3.client(
        "sqs",
        endpoint_url="https://message-queue.api.cloud.yandex.net",
        region_name="ru-central1",
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )

    for message in messages:
        resp = client.send_message(
            QueueUrl=QUEUE_URL, MessageBody=json.dumps({"message": message})
        )
    print(f"Sent messages")
