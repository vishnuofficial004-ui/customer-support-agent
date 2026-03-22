# ─────────────────────────────────────────────
# modules/session.py
#
# The single entry point for Module 1.
#
# The main app calls only process_language_step()
# and gets back a clean response dict.
#
# This file:
#   - Reads the session state
#   - Calls detector.py to understand input
#   - Calls menu.py to form the response
#   - Updates the session state
#   - Returns the result
#
# Nothing outside this file needs to know
# how language detection works internally.
# ─────────────────────────────────────────────

from modules.detector import detect_language
from modules.menu import (
    build_welcome_message,
    build_language_confirmed_message,
    build_invalid_choice_message,
    build_already_selected_message,
    build_human_handoff_message,
    is_handoff_request,
)


def process_language_step(user_input: str, session: dict) -> dict:
    """
    Main entry point for Module 1.

    Parameters:
        user_input : the raw message the customer sent
        session    : dict carrying all conversation state
                     across messages. At minimum contains:
                     {
                       "language_code": str | None,
                       "language_menu_sent": bool,
                       "step": str,
                     }

    Returns a response dict:
        {
          "message":           str | None,
          "language_selected": bool,
          "language_code":     str | None,
          "language_name":     str | None,
          "next_step":         str,
          "session":           dict,   ← updated session
        }

    Why we return the updated session:
    The session is the memory of the conversation.
    Every module reads from it and writes to it.
    By returning it in the response, the caller
    always has the latest state without needing
    a separate function call to update it.
    """

    # ── GUARD 1 — Human handoff request ───────
    # Check this first before anything else.
    # If the customer wants a human, respect it
    # immediately regardless of current step.
    if is_handoff_request(user_input):
        lang_code = session.get("language_code", "en")
        response  = build_human_handoff_message(lang_code)
        session["step"]          = "human_handoff"
        session["handoff_reason"] = "customer_requested"
        response["session"]      = session
        return response

    # ── GUARD 2 — Language already selected ───
    # If language is already in session, skip
    # this entire module and move forward.
    if session.get("language_code"):
        response = build_already_selected_message(
            session["language_code"]
        )
        response["session"] = session
        return response

    # ── STEP 1 — First contact ─────────────────
    # Customer has just messaged for the first
    # time. Send the language menu.
    if not session.get("language_menu_sent"):
        # Try detection on the very first message
        # before showing the menu — catches cases
        # where customer opens with "vanakkam" or
        # types in Tamil script immediately.
        detected = detect_language(user_input)

        if detected:
            # Language clear from first message
            # — skip the menu entirely
            session["language_code"]      = detected["code"]
            session["language_name"]      = detected["name"]
            session["language_menu_sent"] = True
            session["step"]               = "requirements"

            response            = build_language_confirmed_message(detected)
            response["session"] = session
            return response

        # Language not clear — send the menu
        session["language_menu_sent"] = True
        session["step"]               = "await_language_choice"

        response            = build_welcome_message()
        response["session"] = session
        return response

    # ── STEP 2 — Menu already sent ────────────
    # Customer is responding to the language menu.
    # Try to detect their choice.
    detected = detect_language(user_input)

    if detected:
        # Valid choice made
        session["language_code"] = detected["code"]
        session["language_name"] = detected["name"]
        session["step"]          = "requirements"

        response            = build_language_confirmed_message(detected)
        response["session"] = session
        return response

    # ── STEP 3 — Invalid input ─────────────────
    # Customer typed something unrecognized.
    # Resend the menu with an error message.
    # Do NOT update session — stay on this step.
    response            = build_invalid_choice_message()
    response["session"] = session
    return response


def get_session_language(session: dict) -> str:
    """
    Utility — safely retrieves the language code
    from session, defaulting to English.

    Used by Module 2 and Module 3 to know which
    language to respond in without having to
    check if the key exists themselves.
    """
    return session.get("language_code", "en")


def is_language_set(session: dict) -> bool:
    """
    Simple check used by the main conversation
    router to decide whether to run Module 1
    or skip straight to Module 2.
    """
    return bool(session.get("language_code"))


def reset_language(session: dict) -> dict:
    """
    Clears language from session.

    Used in testing and in edge cases where
    a customer explicitly wants to change
    their language mid-conversation.
    """
    session.pop("language_code",      None)
    session.pop("language_name",      None)
    session.pop("language_menu_sent", None)
    session["step"] = "language"
    return session