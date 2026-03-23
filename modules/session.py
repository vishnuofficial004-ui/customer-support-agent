# ─────────────────────────────────────────────
# modules/session.py
#
# Manages conversation history per customer.
#
# Why this exists:
#   Gemini has no memory between API calls.
#   WhatsApp sends each message as a separate
#   HTTP request to our backend.
#   This file bridges that gap — it stores
#   the full conversation history keyed by
#   the customer's phone number, and retrieves
#   it on every new message so Gemini always
#   sees the complete conversation context.
#
# Storage:
#   During development — in-memory Python dict.
#   This resets when the server restarts which
#   is fine for testing. In production we will
#   move this to Django's database so history
#   survives server restarts.
#
# Session structure per customer:
#   {
#     "phone": "+91 98765 43210",
#     "history": [
#       {"role": "user",      "content": "I want a mattress"},
#       {"role": "assistant", "content": "What size is your room?"},
#       ...
#     ],
#     "handoff": False,
#     "created_at": "2024-01-15T10:30:00",
#     "last_active": "2024-01-15T10:35:00",
#   }
# ─────────────────────────────────────────────

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ── In-memory store ────────────────────────
# Keyed by customer phone number.
# Example key: "+919876543210"
# Replaced by database in production.
_sessions: dict = {}

# ── Session expiry ─────────────────────────
# Conversations older than this are reset.
# Why 24 hours: a customer who contacts the
# showroom today and again tomorrow is likely
# starting a fresh inquiry. Keeping stale
# context from yesterday would confuse Gemini.
SESSION_EXPIRY_HOURS = 24

# ── Max history length ─────────────────────
# Gemini has a context window limit.
# Keeping the last 30 messages covers any
# realistic furniture buying conversation
# while staying well within token limits.
MAX_HISTORY_LENGTH = 30


# ═════════════════════════════════════════════
# CORE SESSION FUNCTIONS
# ═════════════════════════════════════════════

def get_session(phone: str) -> dict:
    """
    Retrieves the session for a customer.
    Creates a new empty session if none exists
    or if the existing one has expired.

    Parameters:
        phone : customer's WhatsApp phone number
                used as the unique session key.

    Returns:
        The customer's session dict — always
        returns a valid session, never None.

    Why phone number as key:
        It's the only stable unique identifier
        we get from WhatsApp/Kapso. Unlike names
        or emails, every WhatsApp user has exactly
        one phone number.
    """
    phone = _normalize_phone(phone)

    if phone in _sessions:
        session = _sessions[phone]
        if not _is_expired(session):
            _update_last_active(session)
            logger.info(f"Session found for {phone} — {len(session['history'])} messages in history")
            return session
        else:
            logger.info(f"Session expired for {phone} — creating new session")
            del _sessions[phone]

    session = _create_session(phone)
    _sessions[phone] = session
    logger.info(f"New session created for {phone}")
    return session


def add_message(phone: str, role: str, content: str) -> None:
    """
    Appends a single message to the customer's
    conversation history.

    Parameters:
        phone   : customer's phone number
        role    : "user" or "assistant"
        content : the message text

    Why we call this twice per exchange:
        Once with role="user" after receiving
        the customer's message, and once with
        role="assistant" after getting Gemini's
        response. This builds the alternating
        user/assistant history Gemini expects.

    Example history after 2 exchanges:
        [
          {"role": "user",      "content": "I want a sofa"},
          {"role": "assistant", "content": "What size room do you have?"},
          {"role": "user",      "content": "12x10 feet"},
          {"role": "assistant", "content": "Great! Who will use it?"},
        ]
    """
    phone   = _normalize_phone(phone)
    session = get_session(phone)

    session["history"].append({
        "role":    role,
        "content": content.strip(),
    })

    # Trim history if it exceeds max length
    # Keep the most recent messages
    if len(session["history"]) > MAX_HISTORY_LENGTH:
        session["history"] = session["history"][-MAX_HISTORY_LENGTH:]
        logger.info(f"History trimmed to {MAX_HISTORY_LENGTH} messages for {phone}")

    _update_last_active(session)
    _sessions[phone] = session


def get_history(phone: str) -> list:
    """
    Returns the full conversation history
    for a customer as a list of message dicts.

    This is passed directly to Gemini's
    messages parameter on every API call.

    Returns empty list for new customers —
    Gemini handles first messages naturally.
    """
    phone   = _normalize_phone(phone)
    session = get_session(phone)
    return session.get("history", [])


def set_handoff(phone: str) -> None:
    """
    Marks a session as handed off to a human.

    Once handoff is set, all subsequent messages
    from this customer are routed to Kapso's
    human inbox — Gemini is no longer called.

    Why this flag exists:
    Without it, every message after HANDOFF_REQUESTED
    would still go to Gemini. The flag ensures
    the human agent takes over completely until
    the conversation is resolved.
    """
    phone   = _normalize_phone(phone)
    session = get_session(phone)
    session["handoff"] = True
    _sessions[phone]   = session
    logger.info(f"Handoff flag set for {phone}")


def is_handoff(phone: str) -> bool:
    """
    Checks if this customer's conversation
    has been handed off to a human agent.

    Called by views.py before every message
    to decide whether to call Gemini or
    route directly to Kapso's inbox.
    """
    phone   = _normalize_phone(phone)
    session = get_session(phone)
    return session.get("handoff", False)


def reset_session(phone: str) -> None:
    """
    Completely clears a customer's session.

    Used when:
    - Customer explicitly starts over
    - Human agent resolves the conversation
    - Testing — reset between test cases

    After reset the next message from this
    customer starts a completely fresh
    conversation with Gemini.
    """
    phone = _normalize_phone(phone)
    if phone in _sessions:
        del _sessions[phone]
        logger.info(f"Session reset for {phone}")


def get_session_stats(phone: str) -> dict:
    """
    Returns a summary of the current session.
    Used in tests and for debugging.

    Returns:
        {
          "phone":         "+919876543210",
          "message_count": 6,
          "handoff":       False,
          "created_at":    "2024-01-15T10:30:00",
          "last_active":   "2024-01-15T10:35:00",
          "is_expired":    False,
        }
    """
    phone   = _normalize_phone(phone)
    session = get_session(phone)
    return {
        "phone":         phone,
        "message_count": len(session.get("history", [])),
        "handoff":       session.get("handoff", False),
        "created_at":    session.get("created_at", ""),
        "last_active":   session.get("last_active", ""),
        "is_expired":    _is_expired(session),
    }


# ═════════════════════════════════════════════
# INTERNAL HELPERS
# ═════════════════════════════════════════════

def _normalize_phone(phone: str) -> str:
    """
    Normalizes phone number format.

    Kapso may send phone numbers in different
    formats depending on the customer's country
    code and how they registered on WhatsApp.

    We strip spaces and dashes and ensure
    it starts with + for consistency.

    Examples:
        "91 98765 43210"  → "+919876543210"
        "+91-98765-43210" → "+919876543210"
        "919876543210"    → "+919876543210"
    """
    phone = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    if phone and not phone.startswith("+"):
        phone = "+" + phone

    return phone


def _create_session(phone: str) -> dict:
    """
    Creates a fresh session dict for a
    new or expired customer conversation.
    """
    now = datetime.now().isoformat()
    return {
        "phone":       phone,
        "history":     [],
        "handoff":     False,
        "created_at":  now,
        "last_active": now,
    }


def _is_expired(session: dict) -> bool:
    """
    Checks if a session has exceeded the
    SESSION_EXPIRY_HOURS threshold.

    Compares last_active timestamp against
    current time. Returns True if expired.
    """
    try:
        last_active = datetime.fromisoformat(session.get("last_active", ""))
        expiry_time = last_active + timedelta(hours=SESSION_EXPIRY_HOURS)
        return datetime.now() > expiry_time
    except (ValueError, TypeError):
        return True


def _update_last_active(session: dict) -> None:
    """
    Updates the last_active timestamp
    to the current time.

    Called on every get_session() and
    add_message() to keep the session alive
    as long as the customer is active.
    """
    session["last_active"] = datetime.now().isoformat()


# ═════════════════════════════════════════════
# DEV UTILITY
# ═════════════════════════════════════════════

def get_all_active_sessions() -> dict:
    """
    Returns a summary of all active sessions.
    Used during development to inspect state.

    Never expose this in a production API
    endpoint — it contains customer data.
    """
    summary = {}
    for phone, session in _sessions.items():
        summary[phone] = {
            "message_count": len(session.get("history", [])),
            "handoff":       session.get("handoff", False),
            "last_active":   session.get("last_active", ""),
        }
    return summary