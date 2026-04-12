from app.integrations.groq_client import call_groq
from app.config.constants import LANGUAGE_SCRIPT_MAP

# Example showroom product database (can be replaced with real DB later)
SHOWROOM_PRODUCTS = [
    {"name": "Comfy Sofa 2-seater", "type": "sofa", "price": 18000, "material": "leather", "health_friendly": False},
    {"name": "Ergo Sofa 3-seater", "type": "sofa", "price": 25000, "material": "foam", "health_friendly": True},
    {"name": "Luxury Mattress", "type": "mattress", "price": 22000, "material": "memory foam", "health_friendly": True},
    {"name": "Budget Mattress", "type": "mattress", "price": 15000, "material": "spring", "health_friendly": False},
    # Add more products here
]

async def recommend_product(session: dict) -> str:
    language = session["preferred_language"]
    product_type = session.get("product_type")
    budget = session.get("budget")
    intent = session.get("intent")  # 'health' or 'lifestyle'

    # Filter products by type
    filtered = [p for p in SHOWROOM_PRODUCTS if p["type"] == product_type]

    # Filter by budget
    min_budget, max_budget = parse_budget(budget)

    if min_budget is not None and max_budget is not None:
        filtered = [p for p in filtered if min_budget <= p["price"] <= max_budget]

    # Filter by intent (health preference)
    if intent == "health":
        filtered = [p for p in filtered if p.get("health_friendly")]

    if not filtered:
        return await translate_text(f"Sorry, no {product_type} found matching your requirements.", language)

    # Sort by price ascending
    filtered.sort(key=lambda x: x["price"])

    # Pick top recommendation
    top_product = filtered[0]

    # Compare with others
    comparison_text = ""
    if len(filtered) > 1:
        comparison_text = "Here are similar options: "
        for p in filtered[1:]:
            comparison_text += f"{p['name']} at ₹{p['price']}, "

    # Build final recommendation
    final_text = (
        f"I recommend '{top_product['name']}' priced at ₹{top_product['price']}. {comparison_text}"
        f"Material: {top_product['material']}."
    )

    return await translate_text(final_text, language)


# -----------------------------
# Helper functions
# -----------------------------

def parse_budget(budget: str):
    """
    Safe parsing of budget string.
    """
    try:
        if not budget:
            return None, None

        budget = budget.strip()

        if "-" in budget:
            parts = budget.split("-")
            return int(parts[0]), int(parts[1])

        val = int(budget)
        return val, val + 5000

    except Exception:
        return None, None

async def translate_text(text: str, language: str) -> str:
    """
    Translate any text into user's preferred language using Groq.
    """
    script = LANGUAGE_SCRIPT_MAP.get(language, language)
    prompt = f"""
You are a showroom assistant AI.
RULES:
- Respond ONLY in {language} using {script}
- Keep it short, friendly, and clear
- Do not add extra explanation
Text: {text}
"""
    resp = await call_groq(prompt)
    return resp.strip() if resp else text