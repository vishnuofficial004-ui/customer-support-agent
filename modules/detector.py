# ─────────────────────────────────────────────
# modules/detector.py
#
# Detects the customer's language from their
# typed message using two strategies:
#   1. Unicode script range scanning
#   2. Transliteration keyword matching
#
# No logic from other modules lives here.
# This file has exactly one responsibility.
# ─────────────────────────────────────────────

from modules.constants import (
    UNICODE_SCRIPT_RANGES,
    TRANSLITERATION_KEYWORDS,
    SUPPORTED_LANGUAGES,
)


def detect_by_unicode(text: str) -> str | None:
    """
    Scans every character in the message for
    characters that belong to a known Indian
    language Unicode block.

    Why this approach:
    If a customer types in actual Tamil or Hindi
    script (not transliteration), the characters
    themselves tell us the language instantly —
    no AI call needed, no guessing.

    Returns a language code like 'ta' or 'hi',
    or None if no Indian script characters found.
    """
    for char in text:
        code_point = ord(char)
        for start, end, lang_code in UNICODE_SCRIPT_RANGES:
            if start <= code_point <= end:
                return lang_code
    return None


def detect_by_transliteration(text: str) -> str | None:
    """
    Splits the message into words and checks each
    word against known transliteration keywords.

    Why this approach:
    Most Indian WhatsApp users type their language
    in English letters — 'vanakkam' instead of
    'வணக்கம்'. Unicode detection misses these
    entirely, so we catch them here.

    Returns a language code or None if no
    recognizable keyword found.
    """
    words = text.lower().strip().split()
    for word in words:
        # Strip punctuation from word edges
        clean_word = word.strip(".,!?;:'\"")
        if clean_word in TRANSLITERATION_KEYWORDS:
            detected = TRANSLITERATION_KEYWORDS[clean_word]
            if detected:
                return detected
    return None


def detect_by_menu_choice(user_input: str) -> dict | None:
    """
    Checks if the customer's input is a valid
    menu selection — either a number (1-6)
    or the language name written out.

    Why both number and name:
    Some customers type '2', others type 'Tamil',
    others type 'tamil'. All three should work.

    Returns the full language dict if valid,
    or None if the input doesn't match anything.
    """
    choice = user_input.strip()

    # Direct number input — the expected main flow
    if choice in SUPPORTED_LANGUAGES:
        return SUPPORTED_LANGUAGES[choice]

    # Customer typed the language name instead
    for lang in SUPPORTED_LANGUAGES.values():
        if choice.lower() == lang["name"].lower():
            return lang

    return None


def detect_language(text: str) -> dict | None:
    """
    Master detection function — runs all three
    strategies in order of reliability:

      1. Menu choice      (most explicit — customer chose)
      2. Unicode script   (most certain — script is definitive)
      3. Transliteration  (best effort — keyword matching)

    Why this order:
    Menu choice is the most reliable signal — the
    customer deliberately selected a number. Unicode
    is next because script characters are definitive.
    Transliteration is last because keywords can
    sometimes overlap across languages.

    Returns the full language dict if detected,
    or None if language cannot be determined.
    """

    # Strategy 1 — explicit menu choice
    by_menu = detect_by_menu_choice(text)
    if by_menu:
        return by_menu

    # Strategy 2 — unicode script scanning
    lang_code = detect_by_unicode(text)
    if lang_code:
        return get_language_by_code(lang_code)

    # Strategy 3 — transliteration keywords
    lang_code = detect_by_transliteration(text)
    if lang_code:
        return get_language_by_code(lang_code)

    return None


def get_language_by_code(code: str) -> dict | None:
    """
    Utility — looks up the full language dict
    from just a language code like 'ta' or 'hi'.

    Used internally and also by other modules
    when they only have the code stored in session.
    """
    for lang in SUPPORTED_LANGUAGES.values():
        if lang["code"] == code:
            return lang
    return None