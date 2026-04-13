from app.integrations.groq_client import call_groq
from app.config.constants import LANGUAGE_SCRIPT_MAP


async def generate_persuasion(session: dict, products: list) -> str:
    """
    Convert recommendation into persuasive sales pitch
    """

    language = session["preferred_language"]
    script = LANGUAGE_SCRIPT_MAP.get(language, language)

    intent = session.get("intent")
    budget = session.get("budget")
    product_type = session.get("product_type")

    # Keep only top 2 products
    top_products = products[:2]

    prompt = f"""
You are an expert furniture salesperson.

GOAL:
- Help customer confidently choose ONE product
- Reduce hesitation
- Highlight value clearly

CUSTOMER:
- Intent: {intent}
- Budget: {budget}
- Product: {product_type}

PRODUCT OPTIONS:
{top_products}

RULES:
- Recommend 1 BEST product
- Optionally compare with 1 alternative
- Explain WHY it's best (comfort, durability, value)
- Mention price naturally
- Keep it short (2–3 lines max)
- End with a soft push (question or suggestion)

STYLE:
- Confident
- Helpful
- Human-like
- Not pushy

LANGUAGE:
Respond ONLY in {language} using {script}

OUTPUT:
Final answer only
"""

    resp = await call_groq(prompt)

    return resp.strip() if resp else "This is a great option for you. Would you like to see more details?"