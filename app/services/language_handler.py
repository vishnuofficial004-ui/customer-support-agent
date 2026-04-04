# app/services/language_handler.py

from app.services.grok_client import generate_grok_reply
from app.config import SUPPORTED_LANGUAGES


async def detect_language(message: str, preferred_language: str = None) -> str:
    """
    Detects the language of the message.
    Priority:
    1. If user already selected a language → use that
    2. Try detecting using AI
    3. Fallback to English
    """

    # --- 1. If user already selected language, respect it ---
    if preferred_language:
        return preferred_language

    try:
        # --- 2. Ask Grok to detect language ---
        prompt = f"""
        Identify the language of this message.
        Only return one word from this list: {SUPPORTED_LANGUAGES}

        Message: "{message}"
        """

        detected = await generate_grok_reply(prompt, language="English")
        detected = detected.strip()

        # --- Normalize result ---
        for lang in SUPPORTED_LANGUAGES:
            if lang.lower() in detected.lower():
                return lang

    except Exception as e:
        print(f"Language detection error: {e}")

    # --- 3. Fallback ---
    return "English"