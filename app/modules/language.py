from app.integrations.groq_client import call_groq
from app.config.constants import SUPPORTED_LANGUAGES, LANGUAGE_SCRIPT_MAP
import difflib

LANGUAGE_PROMPT = (
    "Please choose your preferred language: "
    + ", ".join(SUPPORTED_LANGUAGES)
)


# -----------------------------
# 🔥 FUZZY + SMART MATCH
# -----------------------------
def normalize_language_input(text: str) -> str | None:
    normalized = text.strip().lower()

    lang_map = {lang.lower(): lang for lang in SUPPORTED_LANGUAGES}

    # ✅ 1. Exact match
    if normalized in lang_map:
        return lang_map[normalized]

    # ✅ 2. Partial match (sentence contains language)
    for key in lang_map:
        if key in normalized:
            return lang_map[key]

    # ✅ 3. Fuzzy match (handles typos like "englsh", "tmail")
    matches = difflib.get_close_matches(
        normalized,
        lang_map.keys(),
        n=1,
        cutoff=0.6
    )

    if matches:
        return lang_map[matches[0]]

    return None


# -----------------------------
# 🔥 AI LANGUAGE DETECTION
# -----------------------------
async def detect_language_ai(message: str) -> str | None:
    prompt = f"""
Identify the user's preferred language.

RULES:
- Return ONLY one word from:
  {", ".join(SUPPORTED_LANGUAGES)}
- Understand mixed inputs (Tanglish, Hinglish)
- If unclear → return NONE

Message:
{message}
"""
    resp = await call_groq(prompt)

    if not resp:
        return None

    resp = resp.strip()

    return resp if resp in SUPPORTED_LANGUAGES else None


# -----------------------------
# 🔥 MAIN FUNCTION (NON-BLOCKING)
# -----------------------------
async def process_language_step(session: dict, message: str) -> str | None:

    # -----------------------------
    # Try detecting language ALWAYS (silent intelligence)
    # -----------------------------
    detected_language = normalize_language_input(message)

    if not detected_language:
        detected_language = await detect_language_ai(message)

    # -----------------------------
    # CASE 1: First-time detection (NO INTERRUPTION)
    # -----------------------------
    if not session.get("preferred_language"):
        if detected_language:
            session["preferred_language"] = detected_language
            return None  # 🔥 DO NOT interrupt flow

        # Only ask if completely unknown
        return LANGUAGE_PROMPT

    # -----------------------------
    # CASE 2: Mid-conversation switch
    # -----------------------------
    if detected_language and detected_language != session.get("preferred_language"):
        session["preferred_language"] = detected_language

        return await safe_translate(
            "Sure, I will continue in this language.",
            detected_language
        )

    # -----------------------------
    # CASE 3: No action needed
    # -----------------------------
    return None


# -----------------------------
# 🔥 SAFE TRANSLATION
# -----------------------------
async def safe_translate(text: str, language: str) -> str:

    if not language:
        return text

    # ✅ Avoid LLM for English
    if language.lower() == "english":
        return text

    script = LANGUAGE_SCRIPT_MAP.get(language, language)

    prompt = f"""
Translate into {language} using {script}.

RULES:
- Output ONLY in {language}
- No explanation
- No mixing languages
- Keep it natural

Text:
{text}
"""

    resp = await call_groq(prompt)

    return resp.strip() if resp else text