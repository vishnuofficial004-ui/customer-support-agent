from app.integrations.groq_client import call_groq
from app.modules.language import safe_translate
from app.db.products import get_products_by_type, get_all_product_types


# -----------------------------
# MAIN FLOW (STATE MACHINE)
# -----------------------------
async def process_intent_step(session: dict, message: str):

    language = session["preferred_language"]

    # -----------------------------
    # STEP 1: Extract everything ONCE
    # -----------------------------
    extracted = await extract_all_entities(message)

    if not (session.get("intent") and session.get("product_type") and session.get("budget")):
        return await generate_next_question(session, message)

    # -----------------------------
    # STEP 2: ASK MISSING DATA
    # -----------------------------

    # INTENT
    if not session.get("intent"):
        options = ["Health", "Lifestyle"]

        translated_options = [
            await safe_translate(opt, language) for opt in options
        ]

        return {
            "type": "interactive",
            "message": await safe_translate(
                "Why are you buying this product?",
                language
            ),
            "options": translated_options
        }

    # PRODUCT TYPE
    if not session.get("product_type"):
        product_types = get_all_product_types()

        translated_products = [
            await safe_translate(p, language) for p in product_types
        ]

        return {
            "type": "interactive",
            "message": await safe_translate(
                "Which product are you looking for?",
                language
            ),
            "options": translated_products
        }

    # BUDGET
    if not session.get("budget"):
        product_type = session["product_type"]

        products = get_products_by_type(product_type)

        if not products:
            return {
                "type": "text",
                "message": await safe_translate(
                    "Currently this product is not available. Would you like to explore other options?",
                    language
                )
            }

        prices = sorted(set(
            p.get("price") for p in products if p.get("price") is not None
        ))

        if not prices:
            return {
                "type": "text",
                "message": await safe_translate(
                    "Please tell your budget",
                    language
                )
            }

        price_options = [str(p) for p in prices[:5]]

        return {
            "type": "interactive",
            "message": await safe_translate(
                "Select your budget",
                language
            ),
            "options": price_options
        }

    # -----------------------------
    # DONE
    # -----------------------------
    return None


# -----------------------------
# SINGLE LLM CALL
# -----------------------------
async def extract_all_entities(message: str) -> dict:

    prompt = f"""
Extract structured data from user message.

Return STRICT JSON:
{{
  "intent": "...",
  "product_type": "...",
  "budget": "..."
}}

RULES:
- Understand ANY language (English, Tanglish, Hindi, etc.)
- intent: short label (health, comfort, luxury, etc.) or null
- product_type: generic category (sofa, bed, mattress, etc.) or null
- budget: "15000" or "15000-25000" or null
- If not found → null
- DO NOT explain

Message:
{message}
"""

    resp = await call_groq(prompt)

    try:
        import json
        data = json.loads(resp)
        return {
            "intent": data.get("intent"),
            "product_type": data.get("product_type"),
            "budget": data.get("budget")
        }
    except:
        return {}
    
async def generate_next_question(session: dict, message: str) -> dict:
    """
    Dynamically generate next question like a human salesperson
    """

    language = session["preferred_language"]

    intent = session.get("intent")
    product_type = session.get("product_type")
    budget = session.get("budget")

    # Fetch DB context
    product_types = get_all_product_types()

    product_context = ""
    if product_type:
        products = get_products_by_type(product_type)
        prices = sorted(set(p["price"] for p in products if p.get("price")))
        product_context = f"Available prices: {prices[:5]}"

    prompt = f"""
You are a smart showroom salesperson.

GOAL:
- Ask the NEXT best question naturally
- Sound human, not robotic
- Use context to guide conversation

CUSTOMER DATA:
- Intent: {intent}
- Product: {product_type}
- Budget: {budget}

AVAILABLE PRODUCTS:
{product_types}

PRODUCT CONTEXT:
{product_context}

USER MESSAGE:
{message}

RULES:
- Ask ONLY ONE question
- Keep it short
- Make it conversational
- No generic questions
- No repetition
- Move toward purchase decision

LANGUAGE:
Respond in {language}

OUTPUT:
Return ONLY the question text
"""

    question = await call_groq(prompt)

    return {
        "type": "text",
        "message": question.strip() if question else "Can you tell me more about what you're looking for?"
    }