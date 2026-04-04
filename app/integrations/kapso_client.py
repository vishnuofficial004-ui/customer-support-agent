import os
import requests


def send_message(user_id: str, message: str):
    url = os.getenv("KAPSO_API_URL")

    payload = {
        "user_id": user_id,
        "message": message
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('KAPSO_API_KEY')}"
    }

    requests.post(url, json=payload, headers=headers)