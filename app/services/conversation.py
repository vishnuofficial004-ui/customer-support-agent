from app.modules.language import process_language_step, safe_translate
from app.modules.intent import process_intent_step
from app.modules.agent import generate_agent_response
from app.modules.social_proof import check_manager_handoff, detect_user_handoff_intent
from app.modules.seriousness import calculate_seriousness
from app.modules.collections import detect_collection_intent, generate_collections_ui
from app.utils.helpers import extract_user_message, extract_user_id
from app.utils.response_formatter import format_response

sessions = {}


async def handle_incoming_message(payload: dict):

    user_id = extract_user_id(payload)
    message = extract_user_message(payload)

    if not message:
        return format_response("Please send a valid message.")

    # -----------------------------
    # SESSION INIT
    # -----------------------------
    session = sessions.setdefault(user_id, {})

    # -----------------------------
    # 🧠 HISTORY
    # -----------------------------
    session.setdefault("history", [])
    session["history"].append(message)
    session["history"] = session["history"][-10:]

    language = session.get("preferred_language", "English")

    # -----------------------------
    # STEP 1: LANGUAGE
    # -----------------------------
    language_response = await process_language_step(session, message)
    if language_response:
        return format_response(language_response)

    # -----------------------------
    # 🔥 STEP 2: USER HANDOFF (TOP PRIORITY)
    # -----------------------------
    user_requested = await detect_user_handoff_intent(message)

    if user_requested:
        session["handoff"] = True
        reply = await safe_translate(
            "Sure, I’ll connect you to our store manager right away.",
            language
        )
        return format_response(reply)

    # -----------------------------
    # 🛍️ STEP 3: COLLECTIONS (SMART TRIGGER)
    # -----------------------------
    is_collection_query = await detect_collection_intent(message)

    # 👉 Only trigger collections if product not yet chosen
    if is_collection_query and not session.get("product_type"):
        collections_ui = await generate_collections_ui(session)
        return format_response(collections_ui)

    # -----------------------------
    # 🔥 STEP 4: INTENT EXTRACTION FIRST (FIX)
    # -----------------------------
    intent_response = await process_intent_step(session, message)

    # -----------------------------
    # STEP 5: AGENT RESPONSE (AFTER CONTEXT)
    # -----------------------------
    agent_response = await generate_agent_response(session, message)

    if not agent_response:
        agent_response = await safe_translate(
            "I'm here to help you choose the right product. Could you tell me more?",
            language
        )

    # -----------------------------
    # STEP 6: HYBRID RESPONSE
    # -----------------------------
    if intent_response:
        return format_response({
            "type": "hybrid",
            "message": agent_response,
            "next_step": intent_response
        })

    # -----------------------------
    # 🧠 STEP 7: SERIOUSNESS
    # -----------------------------
    score = await calculate_seriousness(session, message)
    session["seriousness_score"] = score

    # -----------------------------
    # 🔥 STEP 8: AI HANDOFF
    # -----------------------------
    auto_trigger = check_manager_handoff(session)

    if auto_trigger and not session.get("handoff"):
        session["handoff"] = True

        handoff_text = await safe_translate(
            "Our store manager can assist you further. Shall I connect you?",
            language
        )

        agent_response += f"\n\n{handoff_text}"

    # -----------------------------
    # ⚡ STEP 9: URGENCY (SMART)
    # -----------------------------
    if score >= 80 and not session.get("handoff"):
        urgency_text = await safe_translate(
            "This product is in high demand right now.",
            language
        )
        agent_response += f"\n\n{urgency_text}"

    return format_response(agent_response)