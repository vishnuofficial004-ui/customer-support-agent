from app.integrations.groq_client import call_groq
from app.config.constants import LANGUAGE_SCRIPT_MAP

INTENT_QUESTIONS = [
    "Are you looking for a product for health reasons or for lifestyle/home use?",
    "What budget range are you considering?",
    "Which product type are you interested in (sofa, bed, mattress, wardrobe, chair)?"
]


async def generate_intent_question(session: dict) -> str:
    """
    Decide which question to ask next based on session state.
    """
    if not session.get("intent"):
        return await translate_question(INTENT_QUESTIONS[0], session["preferred_language"])
    if not session.get("budget"):
        return await translate_question(INTENT_QUESTIONS[1], session["preferred_language"])
    if not session.get("product_type"):
        return await translate_question(INTENT_QUESTIONS[2], session["preferred_language"])
    
    # All captured, return confirmation
    confirmation_text = (
        f"Got it! You are looking for a {session['product_type']} "
        f"for {session['intent']} purposes with a budget of {session['budget']}."
    )
    return await translate_question(confirmation_text, session["preferred_language"])


# session keys:
# intent, intent_confirmed
# budget, budget_confirmed
# product_type, product_confirmed

async def process_intent_step(session: dict, message: str) -> str:
    language = session["preferred_language"]

    # ---------------------
    # Step 1: Intent
    # ---------------------
    if not session.get("intent"):
        intent = await extract_intent(message)
        if not intent:
            return await translate_question(INTENT_QUESTIONS[0], language)
        session["intent"] = intent
        # Instead of compliment, always ask next question
        return await translate_question(INTENT_QUESTIONS[1], language)  # ask budget next

    # ---------------------
    # Step 2: Budget
    # ---------------------
    if not session.get("budget"):
        budget = await extract_budget(message)
        if not budget:
            return await translate_question(INTENT_QUESTIONS[1], language)
        session["budget"] = budget
        return await translate_question(INTENT_QUESTIONS[2], language)  # ask product type

    # ---------------------
    # Step 3: Product Type
    # ---------------------
    if not session.get("product_type"):
        product_type = await extract_product_type(message)
        if not product_type:
            return await translate_question(INTENT_QUESTIONS[2], language)
        session["product_type"] = product_type

    # ---------------------
    # Step 4: Summary confirmation
    # ---------------------
    summary = (
        f"Great! I have noted: Intent: {session['intent']}, "
        f"Budget: {session['budget']}, "
        f"Product: {session['product_type']}. Is this correct?"
    )
    return await translate_question(summary, language)
# -----------------------------
async def extract_intent(message: str) -> str:
    prompt = f"""
You are a showroom AI assistant. Determine the user's intent:
- 'health' if related to back/joint pain or medical reasons
- 'lifestyle' if related to home/living preferences

Respond with 'health' or 'lifestyle' only.
User message: {message}
"""
    resp = await call_groq(prompt)
    return resp.strip().lower() if resp else None


async def extract_budget(message: str) -> str:
    prompt = f"""
Extract numeric budget range from the message.
Respond as min-max or single number.
User message: {message}
"""
    resp = await call_groq(prompt)
    return resp.strip() if resp else None


async def extract_product_type(message: str) -> str:
    prompt = f"""
Identify product type: sofa, bed, mattress, wardrobe, chair.
Respond with exact product type only.
User message: {message}
"""
    resp = await call_groq(prompt)
    return resp.strip().lower() if resp else None


async def translate_question(text: str, language: str) -> str:
    """
    Translate text to user's preferred language with script enforced.
    """
    script = LANGUAGE_SCRIPT_MAP.get(language, language)
    prompt = f"""
You are a showroom AI assistant.
RULES:
- Respond ONLY in {language} using {script}
- Keep it short, friendly, and clear
- Do NOT add extra explanation
Text: {text}
"""
    resp = await call_groq(prompt)
    return resp.strip() if resp else text  # fallback to English if null