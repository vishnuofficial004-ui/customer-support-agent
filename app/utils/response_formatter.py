def format_response(reply):

    if isinstance(reply, str):
        return {
            "type": "text",
            "text": reply.strip('"')
        }

    if isinstance(reply, dict) and reply.get("type") == "interactive":
        return {
            "type": "quick_replies",
            "text": reply.get("message"),
            "options": [
                {"title": opt, "value": opt}
                for opt in reply.get("options", [])
            ]
        }

    if isinstance(reply, dict) and reply.get("type") == "hybrid":
        return {
            "type": "hybrid",
            "text": reply.get("message").strip('"'),
            "next_step": reply.get("next_step")
        }

    return {
        "type": "text",
        "text": str(reply)
    }