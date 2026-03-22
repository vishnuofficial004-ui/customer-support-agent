# ─────────────────────────────────────────────
# modules/menu.py
#
# Handles all outgoing messages for the
# language selection step.
#
# Responsibilities:
#   - Sending the language menu
#   - Confirming the selected language
#   - Handling invalid inputs gracefully
#   - Deciding when to re-send vs move forward
#
# This file forms responses.
# detector.py reads inputs.
# They never do each other's job.
# ─────────────────────────────────────────────

from modules.constants import (
    LANGUAGE_MENU,
    INVALID_CHOICE_MESSAGE,
    SUPPORTED_LANGUAGES,
)


def build_welcome_message() -> dict:
    """
    Returns the very first message sent to
    every new customer who contacts the bot.

    Why a dict and not just a string:
    Every response in this project is a dict
    so the session handler always gets a
    consistent structure — message text,
    what state we're in, what to do next.
    This makes the session handler simple
    and predictable.
    """
    return {
        "message":          LANGUAGE_MENU,
        "language_selected": False,
        "language_code":    None,
        "next_step":        "await_language_choice",
    }


def build_language_confirmed_message(lang: dict) -> dict:
    """
    Sent immediately after the customer
    selects or is auto-detected into a language.

    The greeting in lang["greeting"] is already
    written in the customer's chosen language
    (defined in constants.py) — so this message
    feels native from the very first response.

    Why we include language_code in the return:
    The session handler stores this and passes
    it to every subsequent module so every
    response from Module 2 and Module 3
    is automatically in the right language.
    """
    return {
        "message":          lang["greeting"],
        "language_selected": True,
        "language_code":    lang["code"],
        "language_name":    lang["name"],
        "next_step":        "requirements",
    }


def build_invalid_choice_message() -> dict:
    """
    Sent when the customer types something
    other than 1-6 on the language menu.

    Why we resend the full menu:
    Never just say 'invalid input' and leave
    the customer stuck. Always give them
    exactly what they need to proceed.
    Frustration at this step = lost customer.
    """
    return {
        "message":          INVALID_CHOICE_MESSAGE,
        "language_selected": False,
        "language_code":    None,
        "next_step":        "await_language_choice",
    }


def build_already_selected_message(lang_code: str) -> dict:
    """
    Returned when language is already set
    in the session — skips the menu entirely
    and moves straight to the next module.

    Why this exists:
    If a customer sends multiple messages
    before the bot responds, or if the session
    is replayed, we should never show the
    language menu again once it's been set.
    This prevents a confusing experience where
    a customer who already chose Tamil suddenly
    sees the language menu again mid-conversation.
    """
    return {
        "message":          None,
        "language_selected": True,
        "language_code":    lang_code,
        "next_step":        "requirements",
    }


def build_human_handoff_message(lang_code: str) -> dict:
    """
    Sent when the customer explicitly asks to
    speak to a human during the language step
    (e.g. types 'human', 'agent', 'person').

    Why handle it this early:
    Some customers will bypass the menu and
    immediately ask for a human. We should
    respect that immediately rather than
    forcing them through the language flow.
    """
    handoff_messages = {
        "en": "Sure! Let me connect you with our team right away. Please wait a moment. 🙏",
        "ta": "சரி! உடனே உங்களை எங்கள் குழுவுடன் இணைக்கிறேன். கொஞ்சம் காத்திருங்கள். 🙏",
        "te": "సరే! వెంటనే మీకు మా జట్టుతో అనుసంధానిస్తాను. కొంచెం వేచి ఉండండి. 🙏",
        "kn": "ಸರಿ! ತಕ್ಷಣ ನಿಮ್ಮನ್ನು ನಮ್ಮ ತಂಡದೊಂದಿಗೆ ಸಂಪರ್ಕಿಸುತ್ತೇನೆ. ಸ್ವಲ್ಪ ಕಾಯಿರಿ. 🙏",
        "ml": "ശരി! ഉടൻ നിങ്ങളെ ഞങ്ങളുടെ ടീമുമായി ബന്ധിപ്പിക്കാം. ഒരു നിമിഷം കാത്തിരിക്കൂ. 🙏",
        "hi": "ठीक है! अभी आपको हमारी टीम से जोड़ता हूँ। एक पल रुकिए। 🙏",
    }

    # Default to English if language not yet determined
    message = handoff_messages.get(lang_code, handoff_messages["en"])

    return {
        "message":          message,
        "language_selected": True,
        "language_code":    lang_code or "en",
        "next_step":        "human_handoff",
    }


# ─────────────────────────────────────────────
# Keywords that trigger human handoff
# regardless of what step the customer is on
# ─────────────────────────────────────────────
HANDOFF_TRIGGERS = [
    "human", "agent", "person", "staff",
    "help", "support", "talk", "call",
    "ஆள்", "ஆட்கள்",         # Tamil
    "మనిషి", "సిబ్బంది",      # Telugu
    "ಮನುಷ್ಯ", "ಸಿಬ್ಬಂದಿ",    # Kannada
    "മനുഷ്യൻ", "ജീവനക്കാർ",  # Malayalam
    "इंसान", "कर्मचारी",      # Hindi
]


def is_handoff_request(text: str) -> bool:
    """
    Checks if the customer's message is
    requesting a human agent.

    Called before any other processing so
    a handoff request is always respected
    immediately — no matter what step
    the conversation is currently on.
    """
    text_lower = text.lower().strip()
    return any(trigger in text_lower for trigger in HANDOFF_TRIGGERS)


def get_all_language_names() -> list:
    """
    Utility — returns a simple list of all
    supported language names.

    Used in tests and admin views to
    verify the language list is complete.
    """
    return [lang["name"] for lang in SUPPORTED_LANGUAGES.values()]