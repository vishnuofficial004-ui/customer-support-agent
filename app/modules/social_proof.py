from app.integrations.groq_client import call_groq
from app.config.constants import LANGUAGE_SCRIPT_MAP

# Example database of reviews (replace with real DB)
CUSTOMER_REVIEWS = {
    "mattress": [
        {"intent": "health", "review": "This mattress helped my back pain a lot!"},
        {"intent": "lifestyle", "review": "Very comfortable and stylish for daily use."}
    ],
    "sofa": [
        {"intent": "health", "review": "Good support for elderly parents."},
        {"intent": "lifestyle", "review": "Looks great in my living room!"}
    ],
    # Add more products as needed
}


async def generate_social_proof(session: dict) -> str:
    """
    Generate social proof for the product based on intent.
    """
    language = session["preferred_language"]
    product_type = session.get("product_type")
    intent = session.get("intent")

    reviews = CUSTOMER_REVIEWS.get(product_type, [])
    relevant_reviews = [r["review"] for r in reviews if r["intent"] == intent]

    if not relevant_reviews:
        text = "Customers have liked this product."
    else:
        text = " ".join(relevant_reviews)

    # Translate to preferred language
    return await translate_text(text, language)


async def check_manager_handoff(session: dict) -> bool:
    """
    Determine if the user is serious enough to handoff to manager.
    """
    # Example rule: if all intent, budget, and product_type are confirmed
    if session.get("intent") and session.get("budget") and session.get("product_type") and not session.get("handoff_done"):
        session["handoff_done"] = True
        return True
    return False


async def translate_text(text: str, language: str) -> str:
    """
    Translate text into user's preferred language using Groq.
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