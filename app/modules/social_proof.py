from app.integrations.groq_client import call_groq
from app.config.constants import LANGUAGE_SCRIPT_MAP
from app.db.reviews import get_reviews_by_product  # 🔥 you need this


# -----------------------------
# MAIN: HYBRID SOCIAL PROOF
# -----------------------------
async def generate_social_proof(session: dict) -> str:
    """
    Hybrid model:
    1. Fetch real reviews from DB
    2. AI selects + adapts relevant one
    3. Fallback → AI-generated "common feedback"
    """

    language = session["preferred_language"]
    script = LANGUAGE_SCRIPT_MAP.get(language, language)

    product_type = session.get("product_type")
    intent = session.get("intent")

    # -----------------------------
    # STEP 1: FETCH REAL REVIEWS
    # -----------------------------
    reviews = []
    if product_type:
        reviews = get_reviews_by_product(product_type)

    # -----------------------------
    # STEP 2: FILTER RELEVANT REVIEWS
    # -----------------------------
    relevant_reviews = []

    if reviews and intent:
        for r in reviews:
            tags = [t.lower() for t in r.get("tags", [])]
            if intent.lower() in tags:
                relevant_reviews.append(r["review"])

    # fallback → use any reviews
    if not relevant_reviews and reviews:
        relevant_reviews = [r["review"] for r in reviews]

    # -----------------------------
    # STEP 3: AI ADAPTATION (NOT FAKE)
    # -----------------------------
    if relevant_reviews:
        selected_reviews = relevant_reviews[:3]  # keep prompt small

        prompt = f"""
You are a showroom assistant.

TASK:
- Convert real customer feedback into a natural sentence

INPUT REVIEWS:
{selected_reviews}

RULES:
- DO NOT invent anything new
- Keep meaning same
- Make it conversational
- Keep it SHORT (1–2 lines)

IMPORTANT:
- Do NOT say "review"
- Do NOT exaggerate
- Sound natural

LANGUAGE:
Respond ONLY in {language} using {script}

OUTPUT:
Final sentence only
"""
        resp = await call_groq(prompt)
        return resp.strip() if resp else selected_reviews[0]

    # -----------------------------
    # STEP 4: FALLBACK (SAFE AI)
    # -----------------------------
    fallback_prompt = f"""
Generate a COMMON customer feedback (not a specific review).

CONTEXT:
Product: {product_type}
Intent: {intent}

RULES:
- Do NOT pretend it's real review
- Use phrasing like:
  "Most customers mention..."
  "Many buyers feel..."
- Keep it SHORT
- No exaggeration

LANGUAGE:
Respond ONLY in {language} using {script}
"""
    resp = await call_groq(fallback_prompt)

    return resp.strip() if resp else ""


# -----------------------------
# USER-TRIGGER HANDOFF
# -----------------------------
async def detect_user_handoff_intent(message: str) -> bool:
    """
    STRICT detection for manager/human request
    """

    msg = message.lower()

    # -----------------------------
    # ✅ RULE-BASED (FAST + ACCURATE)
    # -----------------------------
    strong_signals = [
        "talk to manager",
        "speak to manager",
        "connect me to manager",
        "i want human",
        "talk to human",
        "call me",
        "have someone call me",
        "agent venum",
        "manager venum",
        "customer support",
        "representative",
        "real person",
    ]

    for phrase in strong_signals:
        if phrase in msg:
            return True

    # -----------------------------
    # ❌ EARLY EXIT (IMPORTANT)
    # Avoid false positives
    # -----------------------------
    non_handoff_patterns = [
        "what",
        "which",
        "show",
        "tell me",
        "collections",
        "price",
        "details",
        "options"
    ]

    if any(word in msg for word in non_handoff_patterns):
        return False

    # -----------------------------
    # 🧠 AI FALLBACK (STRICT)
    # -----------------------------
    prompt = f"""
Detect if user EXPLICITLY wants to talk to a human.

STRICT RULES:
- Return ONLY YES or NO
- Only YES if CLEAR request for human/manager
- Browsing, questions, product queries → NO

Message:
{message}
"""

    resp = await call_groq(prompt)

    return resp and resp.strip().upper() == "YES"


# -----------------------------
# AI-TRIGGER HANDOFF
# -----------------------------
def check_manager_handoff(session: dict) -> bool:

    score = session.get("seriousness_score", 0)

    if score >= 80:
        return True

    return False


# -----------------------------
# TRANSLATION
# -----------------------------
async def translate_text(text: str, language: str) -> str:

    script = LANGUAGE_SCRIPT_MAP.get(language, language)

    prompt = f"""
Convert into {language} using {script}.

RULES:
- Keep it short
- No explanation
- Do NOT mix languages

Text:
{text}
"""

    resp = await call_groq(prompt)

    return resp.strip() if resp else text