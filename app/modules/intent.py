from app.integrations.groq_client import call_groq
from app.modules.language import safe_translate, enforce_language
from app.db.products import get_products_by_type, get_all_product_types


# -----------------------------
# 🧠 MAIN INTENT STEP
# -----------------------------
async def process_intent_step(session: dict, message: str):

    language = session["preferred_language"]

    extracted = await extract_all_entities(message)

    db_products = get_all_product_types()
    db_products_lower = {p.lower(): p for p in db_products}

    if extracted:

        # -----------------------------
        # ✅ PRODUCT VALIDATION (ROBUST)
        # -----------------------------
        product = extracted.get("product_type")

        if product:
            product_clean = product.strip().lower()

            if not session.get("product_type") and product_clean in db_products_lower:
                session["product_type"] = db_products_lower[product_clean]

            elif product_clean not in db_products_lower:
                return {
                    "type": "text",
                    "message": await safe_translate(
                        f"We don’t have '{product}'. But we do have {', '.join(db_products[:3])}. Would you like to explore these?",
                        language
                    )
                }

        # -----------------------------
        # ✅ INTENT
        # -----------------------------
        if not session.get("intent") and extracted.get("intent"):
            session["intent"] = extracted["intent"]

        # -----------------------------
        # ✅ BUDGET
        # -----------------------------
        if not session.get("budget") and extracted.get("budget"):
            session["budget"] = extracted["budget"]

    # -----------------------------
    # 🔥 ASK NEXT QUESTION
    # -----------------------------
    if not (session.get("intent") and session.get("product_type") and session.get("budget")):
        return await generate_next_question(session, message)

    return None


# -----------------------------
# 🧠 ENTITY EXTRACTION (SAFE JSON)
# -----------------------------
async def extract_all_entities(message: str) -> dict:

    product_types = get_all_product_types()

    prompt = f"""
Return STRICT JSON only:

{{
  "intent": string or null,
  "product_type": string or null,
  "budget": string or null
}}

VALID PRODUCTS:
{product_types}

RULES:
- product_type MUST be from VALID PRODUCTS or null
- budget format: "15000" or "15000-25000"
- If not found → null
- NO explanation
- NO extra text

Message:
{message}
"""

    resp = await call_groq(prompt)

    if not resp:
        return {}

    try:
        import json
        data = json.loads(resp)

        return {
            "intent": data.get("intent"),
            "product_type": data.get("product_type"),
            "budget": data.get("budget")
        }

    except Exception:
        return {}


# -----------------------------
# 💬 HUMAN-LIKE NEXT QUESTION
# -----------------------------
async def generate_next_question(session: dict, message: str) -> dict:

    language = session["preferred_language"]

    intent = session.get("intent")
    product_type = session.get("product_type")
    budget = session.get("budget")

    product_types = get_all_product_types()

    # -----------------------------
    # 📦 PRODUCT CONTEXT
    # -----------------------------
    product_context = ""

    if product_type:
        products = get_products_by_type(product_type)

        prices = sorted(set(
            p.get("price") for p in products if p.get("price") is not None
        ))

        if prices:
            product_context = f"Available prices: {prices[:5]}"

    # -----------------------------
    # 🧠 PROMPT
    # -----------------------------
    prompt = f"""
You are a showroom salesperson.

Ask ONE smart next question.

CUSTOMER:
Intent: {intent}
Product: {product_type}
Budget: {budget}

AVAILABLE:
{product_types}

CONTEXT:
{product_context}

USER:
{message}

RULES:
- Ask ONLY one question
- Be natural
- No repetition
- Move toward purchase
- Do NOT invent products

LANGUAGE:
Respond ONLY in {language}

OUTPUT:
Only the question
"""

    resp = await call_groq(prompt)

    # -----------------------------
    # 🛟 SAFE FALLBACK
    # -----------------------------
    final_text = resp.strip() if resp else "Can you tell me more about what you're looking for?"

    # 🔥 CLEAN + ENFORCE LANGUAGE
    final_text = await enforce_language(final_text, language)

    return {
        "type": "text",
        "message": final_text
    }