# ─────────────────────────────────────────────
# tests/test_language.py
#
# Tests every possible path through Module 1.
#
# We test:
#   - Language menu shown on first contact
#   - Valid menu choice (number input)
#   - Valid menu choice (name input)
#   - Auto-detection via Unicode script
#   - Auto-detection via transliteration
#   - Invalid input handling
#   - Already selected language skip
#   - Human handoff detection
#   - Session state updates correctly
#
# Run with:
#   python -m pytest tests/test_language.py -v
# ─────────────────────────────────────────────

import sys
import os

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.session import (
    process_language_step,
    get_session_language,
    is_language_set,
    reset_language,
)
from modules.detector import (
    detect_by_unicode,
    detect_by_transliteration,
    detect_by_menu_choice,
    detect_language,
)
from modules.menu import is_handoff_request


# ─────────────────────────────────────────────
# Helper — creates a fresh empty session
# ─────────────────────────────────────────────
def new_session():
    return {
        "language_code":      None,
        "language_name":      None,
        "language_menu_sent": False,
        "step":               "language",
    }


# ═════════════════════════════════════════════
# DETECTOR TESTS
# ═════════════════════════════════════════════

class TestDetectByUnicode:

    def test_tamil_script_detected(self):
        result = detect_by_unicode("வணக்கம்")
        assert result == "ta", "Tamil script should return 'ta'"

    def test_telugu_script_detected(self):
        result = detect_by_unicode("నమస్కారం")
        assert result == "te", "Telugu script should return 'te'"

    def test_kannada_script_detected(self):
        result = detect_by_unicode("ನಮಸ್ಕಾರ")
        assert result == "kn", "Kannada script should return 'kn'"

    def test_malayalam_script_detected(self):
        result = detect_by_unicode("നമസ്കാരം")
        assert result == "ml", "Malayalam script should return 'ml'"

    def test_hindi_script_detected(self):
        result = detect_by_unicode("नमस्ते")
        assert result == "hi", "Hindi script should return 'hi'"

    def test_english_returns_none(self):
        result = detect_by_unicode("Hello")
        assert result is None, "English text should return None"

    def test_empty_string_returns_none(self):
        result = detect_by_unicode("")
        assert result is None, "Empty string should return None"


class TestDetectByTransliteration:

    def test_tamil_keyword_vanakkam(self):
        result = detect_by_transliteration("vanakkam")
        assert result == "ta"

    def test_tamil_keyword_in_sentence(self):
        result = detect_by_transliteration("vanakkam naan oru sofa venum")
        assert result == "ta"

    def test_hindi_keyword_chahiye(self):
        result = detect_by_transliteration("mujhe sofa chahiye")
        assert result == "hi"

    def test_hindi_keyword_namaste(self):
        result = detect_by_transliteration("namaste bhai")
        assert result == "hi"

    def test_telugu_keyword(self):
        result = detect_by_transliteration("naku kavali")
        assert result == "te"

    def test_unknown_returns_none(self):
        result = detect_by_transliteration("hello")
        assert result is None

    def test_punctuation_stripped(self):
        # Customer types "vanakkam!" — punctuation should not break detection
        result = detect_by_transliteration("vanakkam!")
        assert result == "ta"


class TestDetectByMenuChoice:

    def test_number_1_returns_english(self):
        result = detect_by_menu_choice("1")
        assert result is not None
        assert result["code"] == "en"

    def test_number_2_returns_tamil(self):
        result = detect_by_menu_choice("2")
        assert result is not None
        assert result["code"] == "ta"

    def test_number_6_returns_hindi(self):
        result = detect_by_menu_choice("6")
        assert result is not None
        assert result["code"] == "hi"

    def test_name_tamil_returns_tamil(self):
        result = detect_by_menu_choice("Tamil")
        assert result is not None
        assert result["code"] == "ta"

    def test_name_lowercase_works(self):
        result = detect_by_menu_choice("tamil")
        assert result is not None
        assert result["code"] == "ta"

    def test_invalid_number_returns_none(self):
        result = detect_by_menu_choice("9")
        assert result is None

    def test_random_word_returns_none(self):
        result = detect_by_menu_choice("hello")
        assert result is None


class TestDetectLanguage:

    def test_menu_choice_takes_priority(self):
        # Number input should resolve via menu choice
        result = detect_language("2")
        assert result is not None
        assert result["code"] == "ta"

    def test_unicode_detected(self):
        result = detect_language("வணக்கம்")
        assert result is not None
        assert result["code"] == "ta"

    def test_transliteration_detected(self):
        result = detect_language("namaste")
        assert result is not None
        assert result["code"] == "hi"

    def test_ambiguous_returns_none(self):
        result = detect_language("hi there")
        assert result is None


# ═════════════════════════════════════════════
# MENU / HANDOFF TESTS
# ═════════════════════════════════════════════

class TestHandoffDetection:

    def test_english_human_trigger(self):
        assert is_handoff_request("I want to talk to a human") is True

    def test_english_agent_trigger(self):
        assert is_handoff_request("agent") is True

    def test_english_help_trigger(self):
        assert is_handoff_request("help") is True

    def test_normal_message_not_handoff(self):
        assert is_handoff_request("I want a sofa") is False

    def test_number_not_handoff(self):
        assert is_handoff_request("2") is False


# ═════════════════════════════════════════════
# SESSION HANDLER TESTS
# ═════════════════════════════════════════════

class TestProcessLanguageStep:

    def test_first_message_shows_menu(self):
        """
        First contact with a neutral message
        should always show the language menu.
        """
        session  = new_session()
        response = process_language_step("Hi", session)

        assert response["language_selected"] is False
        assert response["next_step"] == "await_language_choice"
        assert "1 - English" in response["message"]
        assert response["session"]["language_menu_sent"] is True

    def test_valid_number_choice_locks_language(self):
        """
        After menu is sent, customer types '2'
        — Tamil should be locked in session.
        """
        session                        = new_session()
        session["language_menu_sent"]  = True

        response = process_language_step("2", session)

        assert response["language_selected"] is True
        assert response["language_code"] == "ta"
        assert response["next_step"] == "requirements"
        assert response["session"]["language_code"] == "ta"

    def test_valid_name_choice_locks_language(self):
        """
        Customer types 'Telugu' instead of '3'
        — should still work.
        """
        session                       = new_session()
        session["language_menu_sent"] = True

        response = process_language_step("Telugu", session)

        assert response["language_selected"] is True
        assert response["language_code"] == "te"

    def test_unicode_on_first_message_skips_menu(self):
        """
        Customer's first message is in Tamil script
        — skip the menu entirely, lock Tamil.
        """
        session  = new_session()
        response = process_language_step("வணக்கம்", session)

        assert response["language_selected"] is True
        assert response["language_code"] == "ta"
        assert response["next_step"] == "requirements"

    def test_transliteration_on_first_message_skips_menu(self):
        """
        Customer opens with 'namaste'
        — detect Hindi, skip menu.
        """
        session  = new_session()
        response = process_language_step("namaste", session)

        assert response["language_selected"] is True
        assert response["language_code"] == "hi"

    def test_invalid_choice_resends_menu(self):
        """
        Customer types '9' after menu sent
        — resend menu with error message.
        """
        session                       = new_session()
        session["language_menu_sent"] = True

        response = process_language_step("9", session)

        assert response["language_selected"] is False
        assert response["next_step"] == "await_language_choice"
        assert "1 - English" in response["message"]

    def test_language_already_set_skips_module(self):
        """
        Language already in session
        — skip module entirely, message is None.
        """
        session                  = new_session()
        session["language_code"] = "kn"

        response = process_language_step("anything", session)

        assert response["language_selected"] is True
        assert response["message"] is None
        assert response["next_step"] == "requirements"

    def test_handoff_request_overrides_everything(self):
        """
        Customer types 'agent' at any point
        — immediately route to human handoff.
        """
        session  = new_session()
        response = process_language_step("agent", session)

        assert response["next_step"] == "human_handoff"
        assert response["session"]["step"] == "human_handoff"

    def test_session_updated_after_language_set(self):
        """
        Session dict returned should have
        language_code and step correctly updated.
        """
        session                       = new_session()
        session["language_menu_sent"] = True

        response = process_language_step("1", session)

        assert response["session"]["language_code"] == "en"
        assert response["session"]["step"] == "requirements"


# ═════════════════════════════════════════════
# UTILITY FUNCTION TESTS
# ═════════════════════════════════════════════

class TestSessionUtilities:

    def test_get_session_language_returns_code(self):
        session = {"language_code": "ta"}
        assert get_session_language(session) == "ta"

    def test_get_session_language_defaults_to_english(self):
        session = {}
        assert get_session_language(session) == "en"

    def test_is_language_set_true(self):
        session = {"language_code": "hi"}
        assert is_language_set(session) is True

    def test_is_language_set_false(self):
        session = {"language_code": None}
        assert is_language_set(session) is False

    def test_reset_language_clears_session(self):
        session = {
            "language_code":      "ta",
            "language_name":      "Tamil",
            "language_menu_sent": True,
            "step":               "requirements",
        }
        updated = reset_language(session)
        assert updated.get("language_code") is None
        assert updated.get("language_menu_sent") is None
        assert updated["step"] == "language"


# ─────────────────────────────────────────────
# Run directly with: python tests/test_language.py
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])