def extract_user_id(payload: dict) -> str:
    return payload.get("user_id", "")


def extract_user_message(payload: dict) -> str:
    return payload.get("message", "")