from app.integrations.groq_client import call_groq
from app.config.constants import SUPPORTED_LANGUAGES, LANGUAGE_SCRIPT_MAP
import difflib


LANGUAGE_PROMPT = (
    "Please choose your preferred language: "
    + ", ".join(SUPPORTED_LANGUAGES)
)


# -----------------------------
# 🔍 NORMALIZE LANGUAGE INPUT
# -----------------------------
def normalize_language_input(text: str) -> str | None:
    normalized = text.strip().lower()

    lang_map = {lang.lower(): lang for lang in SUPPORTED_LANGUAGES}

    # ✅ Exact match
    if normalized in lang_map:
        return lang_map[normalized]

    # ✅ Partial match (sentence)
    for key in lang_map:
        if key in normalized:
            return lang_map[key]

    # ✅ Fuzzy match (typos)
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
# 🤖 AI LANGUAGE DETECTION (ROBUST)
# -----------------------------
async def detect_language_ai(message: str) -> str | None:

    prompt = f"""
Detect the user's preferred language.

AVAILABLE:
{", ".join(SUPPORTED_LANGUAGES)}

RULES:
- Return ONLY one word from the list
- No punctuation
- No explanation
- If unclear → return NONE

Message:
{message}
"""

    resp = await call_groq(prompt)

    if not resp:
        return None

    cleaned = resp.strip().lower()

    # Normalize response
    lang_map = {lang.lower(): lang for lang in SUPPORTED_LANGUAGES}

    return lang_map.get(cleaned)


# -----------------------------
# 🧠 MAIN LANGUAGE HANDLER
# -----------------------------
async def process_language_step(session: dict, message: str) -> str | None:

    # Always try detection
    detected_language = normalize_language_input(message)

    if not detected_language:
        detected_language = await detect_language_ai(message)

    # -----------------------------
    # FIRST TIME (NON-BLOCKING)
    # -----------------------------
    if not session.get("preferred_language"):
        if detected_language:
            session["preferred_language"] = detected_language
            return None  # 🔥 DO NOT interrupt flow

        return LANGUAGE_PROMPT

    # -----------------------------
    # MID-CONVERSATION SWITCH
    # -----------------------------
    if detected_language and detected_language != session.get("preferred_language"):
        session["preferred_language"] = detected_language

        return await safe_translate(
            "Sure, I will continue in this language.",
            detected_language
        )

    return None


# -----------------------------
# 🔥 FINAL LANGUAGE ENFORCEMENT
# -----------------------------
async def enforce_language(text: str, language: str) -> str:

    if not text:
        return text

    # ✅ Skip for English (avoid LLM errors)
    if not language or language.lower() == "english":
        return text

    prompt = f"""
Rewrite the following text STRICTLY in {language}.

RULES:
- Output ONLY in {language}
- Do NOT add anything
- Do NOT explain
- Keep meaning EXACT

Text:
{text}
"""

    resp = await call_groq(prompt)

    return resp.strip() if resp else text


# -----------------------------
# 🌍 SAFE TRANSLATION
# -----------------------------
async def safe_translate(text: str, language: str) -> str:

    if not text:
        return text

    # ✅ Avoid LLM for English
    if not language or language.lower() == "english":
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