from app.integrations.groq_client import call_groq


async def calculate_seriousness(session: dict, message: str) -> int:
    """
    Returns a score between 0–100 indicating buying intent
    """

    intent = session.get("intent")
    budget = session.get("budget")
    product = session.get("product_type")

    history = session.get("history", [])

    prompt = f"""
You are an AI that evaluates how serious a customer is about buying.

Score from 0 to 100.

CONSIDER:
- Clarity of requirement
- Budget presence
- Product clarity
- Urgency words (today, now, immediately)
- Decision language (final, confirm, book, buy)

SESSION DATA:
Intent: {intent}
Budget: {budget}
Product: {product}

Conversation:
{history[-5:]}

Latest message:
{message}

RULES:
- Return ONLY a number (0–100)
- No explanation
"""

    resp = await call_groq(prompt)

    try:
        return int(resp.strip())
    except:
        return 50  # safe default