from app.integrations.groq_client import call_groq
from app.db.products import get_all_product_types
from app.modules.language import safe_translate


async def detect_collection_intent(message: str) -> bool:
    msg = message.lower()

    keywords = [
        "collections",
        "what do you have",
        "show products",
        "catalog",
        "range",
        "options"
    ]

    if any(k in msg for k in keywords):
        return True

    prompt = f"""
Detect if user is asking to browse product collections.

RULES:
- Return ONLY YES or NO
- Browsing → YES
- Buying specific product → NO

Message:
{message}
"""

    resp = await call_groq(prompt)
    return resp and resp.strip().upper() == "YES"


async def generate_collections_ui(session: dict):
    language = session.get("preferred_language", "English")

    product_types = get_all_product_types()

    if not product_types:
        return {
            "type": "text",
            "message": await safe_translate(
                "Currently no products are available.",
                language
            )
        }

    return {
        "type": "interactive",
        "message": await safe_translate(
            "Here are our collections:",
            language
        ),
        "options": product_types
    }