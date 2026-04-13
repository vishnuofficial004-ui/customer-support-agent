from app.integrations.groq_client import call_groq
from app.config.constants import LANGUAGE_SCRIPT_MAP
from app.db.products import get_products_by_type


# -----------------------------
# 🧠 CONVERSATION TYPE DETECTION
# -----------------------------
async def detect_conversation_type(message: str) -> str:
    """
    Classifies user message
    """

    prompt = f"""
Classify user message intent.

OPTIONS:
- greeting
- casual
- exploring
- buying
- comparing
- confused

RULES:
- Return ONLY one word
- No explanation

Message:
{message}
"""

    resp = await call_groq(prompt)

    if not resp:
        return "exploring"

    return resp.strip().lower()


# -----------------------------
# 📦 PRODUCT FETCH + SAFE FILTER
# -----------------------------
def get_product_context(session: dict):
    product_type = session.get("product_type")

    if not product_type:
        return []

    products = get_products_by_type(product_type)

    # keep it small + relevant
    return [
        {
            "name": p.get("name"),
            "price": p.get("price"),
            "features": p.get("features", [])
        }
        for p in products[:5]
    ]


# -----------------------------
# 🧠 MAIN AGENT
# -----------------------------
async def generate_agent_response(session: dict, message: str) -> str:

    language = session.get("preferred_language", "English")
    script = LANGUAGE_SCRIPT_MAP.get(language, language)

    intent = session.get("intent")
    budget = session.get("budget")
    product_type = session.get("product_type")

    history = session.get("history", [])[-3:]  # last 3 msgs

    # -----------------------------
    # Detect conversation type
    # -----------------------------
    convo_type = await detect_conversation_type(message)

    # -----------------------------
    # Product context
    # -----------------------------
    product_context = get_product_context(session)

    # -----------------------------
    # Prompt (STRICT CONTROL)
    # -----------------------------
    prompt = f"""
You are a PROFESSIONAL showroom sales assistant.

IMPORTANT:
- Understand any language input
- ALWAYS reply ONLY in {language} using {script}

CONTEXT:
Conversation type: {convo_type}
Intent: {intent}
Budget: {budget}
Product: {product_type}

RECENT CONVERSATION:
{history}

AVAILABLE PRODUCTS:
{product_context}

STRICT RULES:
- Be natural and human-like
- Keep response SHORT (1–2 lines)
- NEVER ignore user's message
- DO NOT ask too many questions
- DO NOT sound robotic
- DO NOT invent products
- If greeting → respond friendly
- If exploring → guide gently
- If buying → recommend confidently
- If confused → simplify

SALES STRATEGY:
- Subtle persuasion
- Build trust
- Guide step-by-step

USER MESSAGE:
{message}

OUTPUT:
Final response only
"""

    resp = await call_groq(prompt)

    return resp.strip() if resp else fallback_response(language)


# -----------------------------
# 🛟 SAFE FALLBACK
# -----------------------------
def fallback_response(language: str) -> str:

    if language.lower() == "tamil":
        return "நான் உதவ தயாராக இருக்கிறேன். நீங்கள் எந்த பொருளை தேடுகிறீர்கள்?"

    if language.lower() == "hindi":
        return "मैं आपकी मदद कर सकता हूँ। आप क्या ढूंढ रहे हैं?"

    return "I'm here to help. What kind of furniture are you looking for?"