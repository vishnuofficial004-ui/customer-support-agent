from app.integrations.groq_client import call_groq
from app.config.constants import SUPPORTED_LANGUAGES, LANGUAGE_SCRIPT_MAP
import difflib


def normalize_language_input(message: str) -> str:
    return message.strip().lower()


def match_language(message: str) -> str | None:
    normalized = normalize_language_input(message)

    language_map = {lang.lower(): lang for lang in SUPPORTED_LANGUAGES}

    matches = difflib.get_close_matches(
        normalized,
        language_map.keys(),
        n=1,
        cutoff=0.75
    )

    if matches:
        return language_map[matches[0]]

    return None


async def process_language_step(session: dict, message: str) -> str:

    # Step 1: Language selection
    if not session.get("preferred_language"):
        matched_language = match_language(message)

        if matched_language:
            session["preferred_language"] = matched_language
            return await generate_confirmation(matched_language)

        return build_language_prompt()

    # Step 2: Detect language (only for tracking)
    detected_language = await detect_language(message)
    session["current_language"] = detected_language

    # Step 3: Always use preferred language
    language = session["preferred_language"]

    response = await generate_response_in_language(message, language)

    return response


def build_language_prompt() -> str:
    return "Please choose your preferred language: " + ", ".join(SUPPORTED_LANGUAGES)


async def detect_language(message: str) -> str:
    prompt = (
        "Identify the language of the following text. "
        "Handle transliterations like Tanglish, Hinglish, Tenglish. "
        "Respond with only the language name.\n\n"
        f"Text: {message}"
    )
    return await call_groq(prompt)


async def generate_confirmation(language: str) -> str:
    script = LANGUAGE_SCRIPT_MAP.get(language, language)

    prompt = f"""
You are a furniture showroom sales assistant.

STRICT RULES:
- Respond ONLY in {language}
- Use ONLY {script}
- Keep response SHORT (1-2 lines)
- Do NOT use any other language

TASK:
- Confirm selected language
- Ask what product they want (sofa, bed, mattress)

OUTPUT:
- Natural, simple, friendly
"""
    return await call_groq(prompt)


async def generate_response_in_language(message: str, language: str) -> str:
    script = LANGUAGE_SCRIPT_MAP.get(language, language)

    prompt = f"""
You are a professional furniture showroom sales assistant. 

RULES:
1. Always respond in {language} using ONLY {script}.
2. Do NOT use English letters, transliteration, or any other language other than the above chosen language.
3. Keep responses short (1-2 lines), friendly, and helpful.
4. Respond only about furniture buying: sofas, beds, mattresses and related products that is present in the showrooms.
5. Ask 1 relevant follow-up question related to what the user wants.
6. Do NOT include extra explanations or unrelated text.
7. keep in mind you should not respond in any other language other than what the language is confirmed even in reply prompts
CONTEXT:
- User is interacting on WhatsApp to buy furniture.
- They may type in their preferred language or mixed/transliterated text.

USER MESSAGE:
{message}

OUTPUT:
- A short, natural, relevant response in {language} using {script}.
"""

    return await call_groq(prompt)