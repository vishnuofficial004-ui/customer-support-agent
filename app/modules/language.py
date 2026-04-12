from app.integrations.groq_client import call_groq
from app.config.constants import SUPPORTED_LANGUAGES, LANGUAGE_SCRIPT_MAP

LANGUAGE_PROMPT = (
    "Please choose your preferred language from the following options: "
    + ", ".join(SUPPORTED_LANGUAGES)
    + "."
)


def normalize_language_input(text: str) -> str | None:
    normalized = text.strip().lower()

    # Exact match
    for lang in SUPPORTED_LANGUAGES:
        if normalized == lang.lower():
            return lang

    # Partial match (e.g., "i want english")
    for lang in SUPPORTED_LANGUAGES:
        if lang.lower() in normalized:
            return lang

    return None


async def process_language_step(session: dict, message: str) -> str | None:
    """
    Handles:
    - Initial language selection
    - Mid-conversation language switching

    Returns:
    - response (str) ONLY if language step handled
    - None if control should move to next step
    """

    detected_language = normalize_language_input(message)

    # -----------------------------
    # 🔥 CASE 1: First time language selection
    # -----------------------------
    if not session.get("preferred_language"):
        if not detected_language:
            return LANGUAGE_PROMPT

        session["preferred_language"] = detected_language
        session["language_selected"] = True

        return await safe_translate(
            "Thanks! Let's get started. What are you looking for?",
            detected_language
        )

    # -----------------------------
    # 🔥 CASE 2: Mid-conversation language switch
    # -----------------------------
    if detected_language and detected_language != session.get("preferred_language"):
        session["preferred_language"] = detected_language

        return await safe_translate(
            "Sure, I will continue in this language. What are you looking for?",
            detected_language
        )

    # -----------------------------
    # 🔥 CASE 3: No language handling needed
    # -----------------------------
    return None


# -----------------------------
# SAFE TRANSLATION (CRITICAL)
# -----------------------------
async def safe_translate(text: str, language: str) -> str:
    """
    Production-safe translation:
    - Avoids LLM for English
    - Strict control for other languages
    """

    # ✅ Skip translation for English (avoid LLM randomness)
    if language.lower() == "english":
        return text

    script = LANGUAGE_SCRIPT_MAP.get(language, language)

    prompt = f"""
You are a STRICT translator.

TASK:
Translate the text into {language}.

RULES:
- Output ONLY in {language}
- Use {script}
- No explanation
- No mixing languages
- Keep meaning EXACT

TEXT:
{text}

OUTPUT:
"""

    resp = await call_groq(prompt)

    if not resp:
        return text

    return resp.strip()