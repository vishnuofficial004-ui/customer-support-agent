def text_response(message: str):
    return {
        "type": "text",
        "message": message
    }


def button_response(message: str, options: list):
    return {
        "type": "buttons",
        "message": message,
        "options": options
    }