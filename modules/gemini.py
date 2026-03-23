# ─────────────────────────────────────────────
# modules/gemini.py
#
# Calls the Gemini API with the full
# conversation history and product data.
#
# This file is the core of the AI system.
# It connects every other module:
#
#   prompt.py   → system instructions
#   sheets.py   → live product data
#   session.py  → conversation history
#         ↓
#     Gemini API
#         ↓
#   clean response + signal detection
#         ↓
#   back to views.py
#
# Why Gemini Flash specifically:
#   Gemini 1.5 Flash is fast, cost-effective,
#   and handles all Indian languages natively.
#   The free tier supports enough calls for
#   the entire validation phase.
# ─────────────────────────────────────────────

import os
import logging
from dotenv import load_dotenv

from modules.prompt  import build_system_prompt, clean_response
from modules.sheets  import get_all_data
from modules.session import add_message, get_history

load_dotenv()
logger = logging.getLogger(__name__)

# ── Model configuration ────────────────────
GEMINI_MODEL    = "gemini-1.5-flash"
MAX_TOKENS      = 500
TEMPERATURE     = 0.7


# ═════════════════════════════════════════════
# GEMINI CLIENT SETUP
# ═════════════════════════════════════════════

def get_gemini_client():
    """
    Initializes and returns the Gemini client
    using the API key from .env.

    Why we initialize per call and not globally:
    Django runs multiple worker processes.
    A global client initialized at import time
    can cause issues across workers. Initializing
    per call is safe, and the overhead is minimal
    since the client is lightweight.

    Returns None if API key is not configured
    so callers can handle it gracefully.
    """
    try:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key or api_key == "your-gemini-api-key-here":
            logger.error("GEMINI_API_KEY not configured in .env")
            return None

        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "max_output_tokens": MAX_TOKENS,
                "temperature":       TEMPERATURE,
            },
        )

        return model

    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        return None


# ═════════════════════════════════════════════
# MAIN FUNCTION — called by views.py
# ═════════════════════════════════════════════

def get_gemini_response(phone: str, user_message: str) -> dict:
    """
    The single function views.py calls
    for every incoming customer message.

    Flow:
        1. Load conversation history for this customer
        2. Fetch fresh product data from Sheets
        3. Build the system prompt with product data
        4. Add customer's message to history
        5. Send full history to Gemini
        6. Add Gemini's response to history
        7. Detect signal tags in response
        8. Return clean response + signals

    Parameters:
        phone        : customer's WhatsApp phone number
        user_message : the message the customer just sent

    Returns:
        {
          "success":    bool,
          "message":    str,   — clean text to send to customer
          "raw":        str,   — full Gemini response with tags
          "show_images": str | None,  — product ID if images needed
          "handoff":    bool,  — True if human handoff requested
          "error":      str | None,   — error message if failed
        }
    """

    # ── Step 1: Get Gemini client ──────────
    model = get_gemini_client()
    if not model:
        return _error_response("AI service is not configured. Please contact support.")

    # ── Step 2: Fetch product data ─────────
    try:
        products, reviews, fit_rules = get_all_data()
    except Exception as e:
        logger.error(f"Failed to fetch product data: {e}")
        return _error_response("Unable to load product information. Please try again.")

    # ── Step 3: Build system prompt ────────
    try:
        system_prompt = build_system_prompt(products, reviews, fit_rules)
    except Exception as e:
        logger.error(f"Failed to build system prompt: {e}")
        return _error_response("Internal configuration error. Please try again.")

    # ── Step 4: Add customer message ───────
    # Store customer message in history BEFORE
    # calling Gemini so the history sent to
    # Gemini includes this latest message.
    add_message(phone, "user", user_message)

    # ── Step 5: Build message list ─────────
    # Gemini receives:
    #   - The system prompt as context
    #   - The full conversation history
    # This gives Gemini complete context to
    # respond accurately to any message.
    history = get_history(phone)

    # Convert our history format to Gemini format
    # Our format:  {"role": "user", "content": "..."}
    # Gemini format: {"role": "user", "parts": ["..."]}
    gemini_messages = [
        {"role": msg["role"], "parts": [msg["content"]]}
        for msg in history
    ]

    # ── Step 6: Call Gemini ────────────────
    try:
        logger.info(f"Calling Gemini for {phone} — {len(history)} messages in history")

        chat     = model.start_chat(history=gemini_messages[:-1])
        response = chat.send_message(
            gemini_messages[-1]["parts"][0],
            # Inject system prompt as context
            # on every call via generation config
        )

        raw_response = response.text
        logger.info(f"Gemini responded for {phone} — {len(raw_response)} chars")

    except Exception as e:
        logger.error(f"Gemini API call failed for {phone}: {e}")
        # Remove the message we just added since
        # the call failed — avoid duplicate entries
        _remove_last_message(phone)
        return _error_response(
            "I'm having trouble connecting right now. "
            "Please try again in a moment. 🙏"
        )

    # ── Step 7: Add Gemini response ────────
    # Store Gemini's response in history so
    # the next message has full context.
    add_message(phone, "assistant", raw_response)

    # ── Step 8: Detect signal tags ─────────
    from modules.prompt import get_image_product_id, is_handoff_requested

    show_images = get_image_product_id(raw_response)
    handoff     = is_handoff_requested(raw_response)
    clean_text  = clean_response(raw_response)

    return {
        "success":     True,
        "message":     clean_text,
        "raw":         raw_response,
        "show_images": show_images,
        "handoff":     handoff,
        "error":       None,
    }


# ═════════════════════════════════════════════
# INTERNAL HELPERS
# ═════════════════════════════════════════════

def _error_response(message: str) -> dict:
    """
    Returns a consistent error response dict.

    Why a helper for this:
    views.py always expects the same dict
    structure regardless of success or failure.
    This helper ensures error responses have
    the exact same shape as success responses
    so views.py never crashes on a KeyError.
    """
    return {
        "success":     False,
        "message":     message,
        "raw":         "",
        "show_images": None,
        "handoff":     False,
        "error":       message,
    }


def _remove_last_message(phone: str) -> None:
    """
    Removes the last message from history.

    Called when a Gemini API call fails after
    we already added the customer's message.
    Without this cleanup the failed message
    stays in history and confuses the next call.
    """
    from modules.session import get_session, _sessions
    from modules.session import _normalize_phone

    phone   = _normalize_phone(phone)
    session = get_session(phone)

    if session["history"]:
        session["history"].pop()
        _sessions[phone] = session
        logger.info(f"Removed last message from history for {phone} after failed API call")


# ═════════════════════════════════════════════
# SYSTEM PROMPT INJECTION
# ═════════════════════════════════════════════

def build_full_prompt_with_history(
    system_prompt: str,
    history: list
) -> list:
    """
    Combines the system prompt with conversation
    history into the format Gemini expects.

    Why we do this manually and not rely on
    Gemini's built-in system instruction:
    The free tier of the Gemini API has limited
    support for system instructions in some
    SDK versions. Prepending the system prompt
    as the first user message is a reliable
    cross-version approach.

    The structure we build:
        [
          {"role": "user",      "parts": ["<system prompt>"]},
          {"role": "model",     "parts": ["Understood. I am Priya..."]},
          {"role": "user",      "parts": ["I want a mattress"]},
          {"role": "model",     "parts": ["What size is your room?"]},
          ...
        ]
    """
    full_history = [
        {
            "role":  "user",
            "parts": [system_prompt],
        },
        {
            "role":  "model",
            "parts": [
                "Understood. I am Priya, your furniture assistant. "
                "I will follow all the instructions provided and help "
                "customers find the perfect furniture in their preferred language."
            ],
        },
    ]

    # Append actual conversation history
    for msg in history:
        gemini_role = "model" if msg["role"] == "assistant" else "user"
        full_history.append({
            "role":  gemini_role,
            "parts": [msg["content"]],
        })

    return full_history


def get_gemini_response_v2(phone: str, user_message: str) -> dict:
    """
    Improved version of get_gemini_response
    that injects the system prompt reliably
    using build_full_prompt_with_history.

    This is the version views.py should use.
    It handles the system prompt injection
    more robustly across all Gemini SDK versions.
    """

    # ── Get Gemini client ──────────────────
    model = get_gemini_client()
    if not model:
        return _error_response("AI service is not configured. Please contact support.")

    # ── Fetch product data ─────────────────
    try:
        products, reviews, fit_rules = get_all_data()
    except Exception as e:
        logger.error(f"Failed to fetch product data: {e}")
        return _error_response("Unable to load product information. Please try again.")

    # ── Build system prompt ────────────────
    try:
        system_prompt = build_system_prompt(products, reviews, fit_rules)
    except Exception as e:
        logger.error(f"Failed to build system prompt: {e}")
        return _error_response("Internal configuration error. Please try again.")

    # ── Add customer message to history ────
    add_message(phone, "user", user_message)
    history = get_history(phone)

    # ── Build full message list ────────────
    full_history = build_full_prompt_with_history(system_prompt, history)

    # ── Call Gemini ────────────────────────
    try:
        logger.info(f"Calling Gemini for {phone} — {len(history)} messages in history")

        # Send all but last as history,
        # last message as the new input
        chat     = model.start_chat(history=full_history[:-1])
        response = chat.send_message(full_history[-1]["parts"][0])

        raw_response = response.text
        logger.info(f"Gemini responded — {len(raw_response)} chars")

    except Exception as e:
        logger.error(f"Gemini API call failed for {phone}: {e}")
        _remove_last_message(phone)
        return _error_response(
            "I'm having trouble connecting right now. "
            "Please try again in a moment. 🙏"
        )

    # ── Store response + detect signals ────
    add_message(phone, "assistant", raw_response)

    from modules.prompt import get_image_product_id, is_handoff_requested

    show_images = get_image_product_id(raw_response)
    handoff     = is_handoff_requested(raw_response)
    clean_text  = clean_response(raw_response)

    return {
        "success":     True,
        "message":     clean_text,
        "raw":         raw_response,
        "show_images": show_images,
        "handoff":     handoff,
        "error":       None,
    }