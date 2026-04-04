from app.modules.language import process_language_step
from app.modules.intent import process_intent_step
from app.modules.recommendation import recommend_product
from app.utils.helpers import extract_user_message, extract_user_id

# In-memory session store
sessions = {}


async def handle_incoming_message(payload: dict):
    """
    Main handler for incoming WhatsApp messages
    """

    user_id = extract_user_id(payload)
    message = extract_user_message(payload)

    if not message:
        return {"reply": "Please send a valid message."}

    # Create session if not exists
    if user_id not in sessions:
        sessions[user_id] = {}

    session = sessions[user_id]

    # -----------------------
    # Step 1: Language selection
    # -----------------------
    if not session.get("preferred_language"):
        response = await process_language_step(session, message)
        return {"reply": response}

    # -----------------------
    # Step 2: Intent + Budget + Product Type Detection
    # -----------------------
    # Only process intent if not all captured yet
    if not (session.get("intent") and session.get("budget") and session.get("product_type")):
        response = await process_intent_step(session, message)
        return {"reply": response}

    # -----------------------
    # Step 3: Product Recommendation
    # -----------------------
    response = await recommend_product(session)
    return {"reply": response}