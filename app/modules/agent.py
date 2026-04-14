from app.integrations.groq_client import call_groq
from app.config.constants import LANGUAGE_SCRIPT_MAP
from app.db.products import get_products_by_type, get_all_product_types
from app.modules.language import enforce_language


# -----------------------------
# 🧠 CONVERSATION TYPE DETECTION (STRICT)
# -----------------------------
async def detect_conversation_type(message: str) -> str:
    prompt = f"""
Classify the user message.

OPTIONS:
greeting, casual, exploring, buying, comparing, confused

RULES:
- Return ONLY one word from options
- NO explanation

Message:
{message}
"""

    resp = await call_groq(prompt)

    if not resp:
        return "exploring"

    clean = resp.strip().lower()

    allowed = {"greeting", "casual", "exploring", "buying", "comparing", "confused"}

    return clean if clean in allowed else "exploring"


# -----------------------------
# 📦 PRODUCT CONTEXT
# -----------------------------
def get_product_context(session: dict):
    product_type = session.get("product_type")

    if not product_type:
        return []

    products = get_products_by_type(product_type)

    return [
        {
            "name": p.get("name"),
            "price": p.get("price"),
            "features": p.get("features", [])
        }
        for p in products[:5]
    ]


# -----------------------------
# 🚫 INVALID PRODUCT DETECTION (DB STRICT)
# -----------------------------
async def detect_invalid_product(message: str, available_products: list) -> str | None:

    prompt = f"""
Check if user is asking for a product NOT in available list.

AVAILABLE PRODUCTS:
{available_products}

RULES:
- If user mentions a product NOT in list → return that word
- If all products are valid → return NONE
- Return ONLY one word
- No explanation

Message:
{message}
"""

    resp = await call_groq(prompt)

    if not resp:
        return None

    result = resp.strip().lower()

    if result == "none":
        return None

    return result


# -----------------------------
# 🛟 RESPONSE CLEANER
# -----------------------------
def clean_llm_output(text: str) -> str | None:

    if not text:
        return None

    lower = text.lower()

    banned_patterns = [
        "classification",
        "intent is",
        "this message is",
        "the message is",
    ]

    for pattern in banned_patterns:
        if pattern in lower:
            return None

    return text.strip()


# -----------------------------
# 🧠 MAIN AGENT
# -----------------------------
async def generate_agent_response(session: dict, message: str) -> str:

    language = session.get("preferred_language", "English")
    script = LANGUAGE_SCRIPT_MAP.get(language, language)

    intent = session.get("intent")
    budget = session.get("budget")
    product_type = session.get("product_type")

    history = session.get("history", [])[-3:]

    # -----------------------------
    # 🚫 STRICT PRODUCT VALIDATION
    # -----------------------------
    all_products = get_all_product_types()

    invalid_product = await detect_invalid_product(message, all_products)

    if invalid_product:
        response = f"Sorry, we don’t have {invalid_product}. We currently offer {', '.join(all_products)}. Would you like to explore these?"
        return await enforce_language(response, language)

    # -----------------------------
    # 🧠 Conversation type
    # -----------------------------
    convo_type = await detect_conversation_type(message)

    # -----------------------------
    # 📦 Product context
    # -----------------------------
    product_context = get_product_context(session)

    # -----------------------------
    # 🧠 PROMPT
    # -----------------------------
    prompt = f"""
You are a PROFESSIONAL showroom sales assistant.

CRITICAL RULES:
- Reply ONLY in {language} using {script}
- DO NOT use any other language
- DO NOT output system text
- DO NOT explain classification
- DO NOT invent products

CONTEXT:
Conversation type: {convo_type}
Intent: {intent}
Budget: {budget}
Product: {product_type}

RECENT:
{history}

AVAILABLE PRODUCTS:
{product_context}

BEHAVIOR:
- greeting → respond warmly
- casual → engage naturally
- exploring → guide
- buying → recommend confidently
- confused → simplify

STYLE:
- 1–2 lines only
- Natural human tone
- Not robotic

USER:
{message}

OUTPUT:
Only final response
"""

    resp = await call_groq(prompt)

    # -----------------------------
    # 🧹 CLEAN OUTPUT
    # -----------------------------
    cleaned = clean_llm_output(resp)

    if not cleaned:
        return await enforce_language(fallback_response(language), language)

    # -----------------------------
    # 🌍 FINAL LANGUAGE ENFORCEMENT
    # -----------------------------
    cleaned = await enforce_language(cleaned, language)

    return cleaned


# -----------------------------
# 🛟 SAFE FALLBACK
# -----------------------------
def fallback_response(language: str) -> str:

    if language.lower() == "tamil":
        return "நான் உதவ தயாராக இருக்கிறேன். நீங்கள் என்ன தேடுகிறீர்கள்?"

    if language.lower() == "hindi":
        return "मैं आपकी मदद कर सकता हूँ। आप क्या ढूंढ रहे हैं?"

    return "I'm here to help. What are you looking for today?"