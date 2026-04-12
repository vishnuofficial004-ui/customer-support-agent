from app.modules.language import process_language_step
from app.modules.intent import process_intent_step
from app.modules.agent import generate_agent_response
from app.modules.social_proof import check_manager_handoff
from app.utils.helpers import extract_user_message, extract_user_id

# Session storage (replace with Redis later)
sessions = {}


async def handle_incoming_message(payload: dict):

    user_id = extract_user_id(payload)
    message = extract_user_message(payload)

    if not message:
        return {"reply": "Please send a valid message."}

    # -----------------------------
    # SESSION INIT
    # -----------------------------
    if user_id not in sessions:
        sessions[user_id] = {}

    session = sessions[user_id]

    # -----------------------------
    # STEP 1: LANGUAGE (NON-BLOCKING)
    # -----------------------------
    language_response = await process_language_step(session, message)

    if language_response:
        return {"reply": language_response}

    # -----------------------------
    # STEP 2: ALWAYS EXTRACT INTENT (NON-BLOCKING)
    # -----------------------------
    intent_response = await process_intent_step(session, message)

    # 👉 If system needs structured input → return interactive UI
    if intent_response:
        return {"reply": intent_response}

    # -----------------------------
    # STEP 3: AI AGENT (ALWAYS ACTIVE)
    # -----------------------------
    agent_response = await generate_agent_response(session, message)

    # -----------------------------
    # STEP 4: MANAGER HANDOFF
    # -----------------------------
    handoff_needed = await check_manager_handoff(session)

    if handoff_needed:
        agent_response += "\n\nA manager will contact you shortly."

    return {"reply": agent_response}