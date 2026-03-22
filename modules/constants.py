# ─────────────────────────────────────────────
# modules/language/constants.py
#
# All static language data lives here.
# No logic — only data definitions.
# ─────────────────────────────────────────────

SUPPORTED_LANGUAGES = {
    "1": {
        "code":     "en",
        "name":     "English",
        "greeting": (
            "Hello! I'm your furniture assistant. 😊\n"
            "I'll help you find the perfect product for your needs.\n"
            "Let's get started!"
        ),
    },
    "2": {
        "code":     "ta",
        "name":     "Tamil",
        "greeting": (
            "வணக்கம்! நான் உங்கள் தளபாட உதவியாளர். 😊\n"
            "உங்களுக்கு சரியான தயாரிப்பு கண்டுபிடிக்க உதவுவேன்.\n"
            "தொடங்கலாமா!"
        ),
    },
    "3": {
        "code":     "te",
        "name":     "Telugu",
        "greeting": (
            "నమస్కారం! నేను మీ ఫర్నిచర్ సహాయకుడిని. 😊\n"
            "మీకు సరైన ఉత్పత్తి కనుగొనడంలో సహాయం చేస్తాను.\n"
            "మొదలు పెట్టవచ్చా!"
        ),
    },
    "4": {
        "code":     "kn",
        "name":     "Kannada",
        "greeting": (
            "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಫರ್ನಿಚರ್ ಸಹಾಯಕ. 😊\n"
            "ನಿಮಗೆ ಸರಿಯಾದ ಉತ್ಪನ್ನ ಹುಡುಕಲು ಸಹಾಯ ಮಾಡುತ್ತೇನೆ.\n"
            "ಪ್ರಾರಂಭಿಸೋಣ!"
        ),
    },
    "5": {
        "code":     "ml",
        "name":     "Malayalam",
        "greeting": (
            "നമസ്കാരം! ഞാൻ നിങ്ങളുടെ ഫർണിച്ചർ അസിസ്റ്റന്റ് ആണ്. 😊\n"
            "നിങ്ങൾക്ക് അനുയോജ്യമായ ഉൽപ്പന്നം കണ്ടെത്താൻ സഹായിക്കാം.\n"
            "തുടങ്ങാം!"
        ),
    },
    "6": {
        "code":     "hi",
        "name":     "Hindi",
        "greeting": (
            "नमस्ते! मैं आपका फर्नीचर सहायक हूँ। 😊\n"
            "आपके लिए सही उत्पाद खोजने में मदद करूंगा।\n"
            "शुरू करते हैं!"
        ),
    },
}

# ─────────────────────────────────────────────
# The first message every new customer receives
# ─────────────────────────────────────────────
LANGUAGE_MENU = (
    "Welcome to our Furniture Store! 🏠\n\n"
    "Please select your language / மொழியை தேர்ந்தெடுக்கவும்:\n\n"
    "1 - English\n"
    "2 - தமிழ் (Tamil)\n"
    "3 - తెలుగు (Telugu)\n"
    "4 - ಕನ್ನಡ (Kannada)\n"
    "5 - മലയാളം (Malayalam)\n"
    "6 - हिंदी (Hindi)\n\n"
    "Reply with the number (1–6)"
)

# ─────────────────────────────────────────────
# Sent when customer types something invalid
# on the language menu
# ─────────────────────────────────────────────
INVALID_CHOICE_MESSAGE = (
    "❗ Please reply with a number between 1 and 6.\n\n"
    + LANGUAGE_MENU
)

# ─────────────────────────────────────────────
# Unicode script ranges for auto-detection
# Maps range → language code
# ─────────────────────────────────────────────
UNICODE_SCRIPT_RANGES = [
    (0x0B80, 0x0BFF, "ta"),   # Tamil
    (0x0C00, 0x0C7F, "te"),   # Telugu
    (0x0C80, 0x0CFF, "kn"),   # Kannada
    (0x0D00, 0x0D7F, "ml"),   # Malayalam
    (0x0900, 0x097F, "hi"),   # Devanagari — Hindi
]

# ─────────────────────────────────────────────
# Common transliteration keywords
# Maps word → language code
# None means the word is ambiguous (e.g. "sofa")
# ─────────────────────────────────────────────
TRANSLITERATION_KEYWORDS = {
    # Tamil
    "vanakkam":  "ta",
    "naan":      "ta",
    "enakku":    "ta",
    "romba":     "ta",
    "enna":      "ta",
    "venum":     "ta",
    "illai":     "ta",

    # Telugu
    "meeru":     "te",
    "ayya":      "te",
    "em":        "te",
    "cheppandi": "te",
    "kavali":    "te",

    # Kannada
    "neevu":     "kn",
    "avaru":     "kn",
    "illa":      "kn",
    "beku":      "kn",
    "sari":      "kn",

    # Malayalam
    "ningal":    "ml",
    "enthu":     "ml",
    "undo":      "ml",
    "veno":      "ml",
    "anu":       "ml",

    # Hindi
    "namaste":   "hi",
    "mujhe":     "hi",
    "chahiye":   "hi",
    "kitna":     "hi",
    "bhai":      "hi",
    "yeh":       "hi",
    "kya":       "hi",
    "hai":       "hi",
    "hain":      "hi",
}