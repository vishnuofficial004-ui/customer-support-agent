from app.integrations.groq_client import call_groq
from app.config.constants import LANGUAGE_SCRIPT_MAP
from app.db.products import get_products_by_type, get_all_product_types


def filter_products(products, budget: str, intent: str):
    """
    Filter and rank products based on budget + intent
    """

    if not products:
        return []

    filtered = products

    # -----------------------------
    # Budget filtering
    # -----------------------------
    try:
        if budget:
            if "-" in budget:
                min_b, max_b = map(int, budget.split("-"))
                filtered = [p for p in filtered if min_b <= p.get("price", 0) <= max_b]
            else:
                val = int(budget)
                filtered = [
                    p for p in filtered
                    if abs(p.get("price", 0) - val) <= 5000
                ]
    except Exception:
        pass  # never break flow

    # -----------------------------
    # If nothing matches → fallback to all
    # -----------------------------
    if not filtered:
        filtered = products

    # -----------------------------
    # Intent-based ranking (dynamic, not hardcoded)
    # -----------------------------
    def score(p):
        s = 0

        # Soft intent matching (no strict hardcoding)
        features = " ".join(p.get("features", [])).lower()

        if intent and intent != "unknown":
            if intent in features:
                s += 2

        # Budget proximity scoring
        if budget:
            try:
                target = int(budget.split("-")[0])
                s += max(0, 2 - abs(p.get("price", 0) - target) // 10000)
            except:
                pass

        return s

    filtered.sort(key=score, reverse=True)

    return filtered[:5]


async def generate_agent_response(session: dict, message: str) -> str:
    language = session["preferred_language"]
    script = LANGUAGE_SCRIPT_MAP.get(language, language)

    intent = session.get("intent")
    budget = session.get("budget")
    product_type = session.get("product_type")

    # -----------------------------
    # Validate product availability
    # -----------------------------
    available_types = get_all_product_types()

    if not product_type or product_type not in available_types:
        prompt = f"""
You are a furniture showroom assistant.

Customer asked for a product which is not available.

AVAILABLE CATEGORIES:
{available_types}

TASK:
- Politely say it's not available
- Suggest closest alternatives
- Keep it short
- Respond ONLY in {language} using {script}

USER MESSAGE:
{message}
"""
        return await call_groq(prompt)

    # -----------------------------
    # Fetch products
    # -----------------------------
    products = get_products_by_type(product_type)

    if not products:
        prompt = f"""
You are a showroom assistant.

We currently don't have this product in stock.

AVAILABLE CATEGORIES:
{available_types}

TASK:
- Inform politely
- Suggest other categories
- Keep it short
- Respond ONLY in {language} using {script}

USER MESSAGE:
{message}
"""
        return await call_groq(prompt)

    # -----------------------------
    # Filter + rank
    # -----------------------------
    filtered_products = filter_products(products, budget, intent)

    # -----------------------------
    # Handle no filtered results
    # -----------------------------
    if not filtered_products:
        filtered_products = products[:3]

    # -----------------------------
    # Prepare context
    # -----------------------------
    product_context = [
        {
            "name": p.get("name"),
            "price": p.get("price"),
            "features": p.get("features", [])
        }
        for p in filtered_products
    ]

    # -----------------------------
    # Prompt
    # -----------------------------
    prompt = f"""
You are a HIGHLY SKILLED furniture showroom sales assistant.

IMPORTANT:
- User may speak in any language (English, Tanglish, Hindi, etc.)
- You MUST understand it
- But ALWAYS reply ONLY in {language} using {script}

YOUR GOAL:
- Recommend best product from AVAILABLE PRODUCTS
- Help customer decide quickly
- Move toward purchase

AVAILABLE PRODUCTS:
{product_context}

CUSTOMER PROFILE:
- Intent: {intent}
- Budget: {budget}
- Product Interest: {product_type}

STRICT RULES:
- DO NOT invent products
- Recommend max 1–2 products
- Mention price naturally
- Keep response SHORT (1–2 lines)
- Ask 1 smart follow-up question

STYLE:
- Natural, human-like
- Confident
- Sales-focused (but not pushy)
- No generic lines

USER MESSAGE:
{message}

OUTPUT:
- Final answer only
"""

    return await call_groq(prompt)