from app.modules.language import process_language_step
from app.modules.intent import process_intent_step
from app.modules.agent import generate_agent_response
from app.modules.social_proof import check_manager_handoff, detect_user_handoff_intent
from app.modules.seriousness import calculate_seriousness
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
    # 🧠 STEP 0: STORE HISTORY
    # -----------------------------
    session.setdefault("history", [])
    session["history"].append(message)
    session["history"] = session["history"][-10:]

    # -----------------------------
    # STEP 1: LANGUAGE (SILENT)
    # -----------------------------
    language_response = await process_language_step(session, message)

    # Only respond if explicitly needed (rare)
    if language_response:
        return {"reply": language_response}

    # -----------------------------
    # 🔥 STEP 2: USER HANDOFF (HIGH PRIORITY)
    # -----------------------------
    user_requested = await detect_user_handoff_intent(message)

    if user_requested:
        session["handoff"] = True
        return {
            "reply": "Sure, I’ll connect you to our store manager right away."
        }

    # -----------------------------
    # 🔥 STEP 3: ALWAYS RESPOND FIRST (CORE FIX)
    # -----------------------------
    agent_response = await generate_agent_response(session, message)

    # -----------------------------
    # STEP 4: EXTRACT INTENT (BACKGROUND)
    # -----------------------------
    intent_response = await process_intent_step(session, message)

    # If system needs structured input → append (NOT replace)
    if intent_response:
        return {
            "reply": {
                "type": "hybrid",
                "message": agent_response,
                "next_step": intent_response
            }
        }

    # -----------------------------
    # 🧠 STEP 5: SERIOUSNESS SCORING
    # -----------------------------
    score = await calculate_seriousness(session, message)
    session["seriousness_score"] = score

    # -----------------------------
    # 🔥 STEP 6: AI HANDOFF
    # -----------------------------
    auto_trigger = check_manager_handoff(session)

    if auto_trigger and not session.get("handoff"):
        session["handoff"] = True
        agent_response += "\n\nOur store manager can assist you further. Shall I connect you now?"

    # -----------------------------
    # ⚡ STEP 7: URGENCY BOOST
    # -----------------------------
    if score >= 70:
        agent_response += "\n\nThis product is in high demand right now."

    return {"reply": agent_response}