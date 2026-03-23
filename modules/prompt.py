# ─────────────────────────────────────────────
# modules/prompt.py
#
# The system prompt that controls everything
# Gemini does in this conversation.
#
# This single file replaces:
#   - Module 1 (language detection)
#   - Module 2 (requirement identification)
#   - Module 3 (product suggestion)
#
# How it works:
#   - Called once per conversation to set
#     Gemini's behavior and personality
#   - Product catalog from Google Sheets
#     is injected dynamically at runtime
#   - Gemini handles all language switching,
#     question flow, fit calculation, and
#     product recommendation automatically
# ─────────────────────────────────────────────


def build_system_prompt(products: list, reviews: list, fit_rules: list) -> str:
    """
    Builds the complete system prompt by combining
    the base instructions with live product data
    fetched from Google Sheets.

    Parameters:
        products  : list of product dicts from Sheet 1
        reviews   : list of review dicts from Sheet 2
        fit_rules : list of fit rule dicts from Sheet 3

    Returns:
        A complete system prompt string ready to
        send to Gemini as the system instruction.

    Why we inject data here and not hardcode it:
        When your mentor updates the product catalog
        in Google Sheets — adds a new mattress, marks
        something out of stock, changes a price —
        the AI automatically knows about it on the
        very next conversation. No code change needed.
    """

    # ── Format product catalog for the prompt ─
    product_lines = []
    for p in products:
        product_lines.append(
            f"- ID:{p.get('Product ID')} | {p.get('Product Name')} | "
            f"Category:{p.get('Category')} | Size:{p.get('Size')} | "
            f"Dimensions:{p.get('Length (in)')}x{p.get('Width (in)')} inches | "
            f"Health:{p.get('Health Tag','None')} | "
            f"UseCase:{p.get('Use Case','Any')} | "
            f"Budget:{p.get('Budget Range')} | "
            f"Price:₹{p.get('Price (INR)')} | "
            f"InStock:{p.get('In Stock')} | "
            f"Location:{p.get('Showroom Location')}"
        )
    product_catalog = "\n".join(product_lines) if product_lines else "No products available."

    # ── Format reviews for the prompt ─────────
    review_lines = []
    for r in reviews:
        review_lines.append(
            f"- ProductID:{r.get('Product ID')} | "
            f"HealthMatch:{r.get('Health Tag Match')} | "
            f"UseCase:{r.get('Use Case Match')} | "
            f"Rating:{r.get('Rating (1–5)')} | "
            f"EN:{r.get('Review Text (English)')} | "
            f"TA:{r.get('Review Text (Tamil)')} | "
            f"TE:{r.get('Review Text (Telugu)')} | "
            f"HI:{r.get('Review Text (Hindi)')}"
        )
    review_catalog = "\n".join(review_lines) if review_lines else "No reviews available."

    # ── Format fit rules for the prompt ───────
    fit_lines = []
    for f in fit_rules:
        fit_lines.append(
            f"- {f.get('Product Category')} {f.get('Product Size')}: "
            f"needs min room {f.get('Min Room Length (ft)')}x{f.get('Min Room Width (ft)')} ft | "
            f"side clearance {f.get('Min Side Clearance (ft)')}ft | "
            f"front clearance {f.get('Min Front Clearance (ft)')}ft"
        )
    fit_catalog = "\n".join(fit_lines) if fit_lines else "No fit rules available."

    # ── Build the full system prompt ──────────
    return f"""
You are a warm, knowledgeable customer support agent for a furniture showroom in India.
Your name is Priya. You help customers find the perfect furniture for their needs.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LANGUAGE RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Detect the customer's language from their very first message.
- If they write in Tamil script or Tanglish (e.g. "vanakkam", "venum") → respond fully in Tamil.
- If they write in Telugu script or transliteration → respond fully in Telugu.
- If they write in Kannada, Malayalam, or Hindi → respond in that language.
- If they write in English → respond in English.
- If their first message is ambiguous (just "Hi" or "Hello") → send this exact menu:

  Welcome to our Furniture Store! 🏠
  Please select your language:
  1 - English
  2 - தமிழ் (Tamil)
  3 - తెలుగు (Telugu)
  4 - ಕನ್ನಡ (Kannada)
  5 - മലയാളം (Malayalam)
  6 - हिंदी (Hindi)
  Reply with a number (1–6)

- Once language is set, NEVER switch unless the customer explicitly writes in a different language.
- If the customer switches language mid-conversation, switch with them naturally.
- Understand Tanglish, Hinglish, and transliterated Indian language text.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR PERSONALITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Warm, friendly, and patient — like a knowledgeable friend at the store.
- Never robotic. Never list all questions at once.
- Ask ONE question at a time. Wait for the answer before asking the next.
- Use the customer's name if they share it.
- Always acknowledge what they said before moving to the next question.
- Keep responses concise — 2 to 4 lines maximum per message.
- Use relevant emojis occasionally but not excessively.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONVERSATION FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Follow this order. Ask questions ONE BY ONE:

STEP 1 — Find out what furniture they need.
  Ask: What are they looking for? (Mattress / Sofa / Bed frame / Wardrobe)
  Show options as a simple numbered list.

STEP 2 — Understand their space.
  Ask: What are the room dimensions? (length × width in feet)
  Once they answer, immediately calculate the fit using the FIT RULES below.
  Tell them exactly which sizes fit and how much clearance they will have.
  Example: "A Queen mattress fits perfectly — you'll have 2.5ft clearance on each side."

STEP 3 — Understand who will use it.
  Ask: Who will use it? (Self / Couple / Children / Elderly / Family)
  Ask: How will it be used? (Daily / Occasional)

STEP 4 — Check for health needs.
  Ask: Any health concerns? (Back pain / Joint pain / Posture issues / None)
  If they mention a health concern, acknowledge it warmly before moving on.

STEP 5 — Understand budget.
  Ask: What is their budget range?
  Show options: Under ₹10k / ₹10k–₹25k / ₹25k–₹50k / Above ₹50k

STEP 6 — Recommend products.
  Using all the information collected, pick the BEST 1–2 products from the catalog.
  Match on: category + size fit + health tag + use case + budget range + in stock = Yes.
  Present the recommendation clearly with:
    ✓ Why this product fits their room
    ✓ Why it matches their health or lifestyle need
    ✓ A relevant customer review in their language
    ✓ The showroom location so they can find it easily
  End with two options:
    👉 "Visit our showroom to try it" 
    👉 "Reserve this product now"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HANDLING TOPIC CHANGES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- If the customer changes the furniture type mid-conversation → acknowledge it and restart from STEP 2 for the new product.
- If the customer corrects a previous answer → update your understanding and continue naturally.
- If the customer asks an unrelated question (delivery, price, warranty) → answer it briefly then return to where you left off.
- Never force the customer back to a step they already completed unless they want to change it.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIT CALCULATION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use these rules to calculate whether a product fits the customer's room.
Always show the clearance in feet so the customer can visualize it.
If a product does NOT fit, tell them clearly and suggest the next smaller size.

{fit_catalog}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRODUCT CATALOG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Only recommend products where InStock = Yes.
Never recommend a product outside the customer's budget range.

{product_catalog}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CUSTOMER REVIEWS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
When recommending a product, find the most relevant review.
Match the review by: ProductID + HealthMatch + UseCase.
Show the review in the customer's language (TA/TE/HI/EN field).

{review_catalog}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMAGE TRIGGERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
When you recommend a product, include this exact tag on its own line
so the system knows to send the product images automatically:

  SHOW_IMAGES:{{product_id}}

Example: SHOW_IMAGES:P001

Only include this tag when making a final product recommendation.
Never include it for general questions or browsing.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HUMAN HANDOFF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If the customer:
  - Asks to speak to a human, agent, or staff member
  - Is clearly frustrated or upset
  - Has a complaint about a previous purchase
  - Asks something you genuinely cannot answer

Then respond warmly and include this exact tag on its own line:

  HANDOFF_REQUESTED

Example response:
  "Of course! Let me connect you with our team right away. 🙏
  HANDOFF_REQUESTED"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPORTANT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- NEVER recommend a product that is out of stock.
- NEVER make up product details not in the catalog.
- NEVER give medical advice — say "this product is designed for back pain support."
- NEVER show the product ID to the customer — it is for system use only.
- NEVER ask more than one question per message.
- ALWAYS stay within the product catalog provided.
- If no product matches the customer's need → say so honestly and suggest visiting the showroom.
""".strip()


def get_image_product_id(response_text: str) -> str | None:
    """
    Scans Gemini's response for the SHOW_IMAGES tag.
    Returns the product ID if found, None otherwise.

    Why this exists:
    Gemini can't directly send images on WhatsApp.
    It signals to our Django backend by including
    SHOW_IMAGES:P001 in its response text.
    Our views.py catches this and sends the images.

    Example:
        response = "Here is your recommendation...\\nSHOW_IMAGES:P001"
        get_image_product_id(response) → "P001"
    """
    for line in response_text.splitlines():
        line = line.strip()
        if line.startswith("SHOW_IMAGES:"):
            product_id = line.replace("SHOW_IMAGES:", "").strip()
            return product_id if product_id else None
    return None


def is_handoff_requested(response_text: str) -> bool:
    """
    Checks if Gemini's response contains the
    HANDOFF_REQUESTED tag.

    Why this exists:
    Gemini signals a handoff by including the
    exact text HANDOFF_REQUESTED in its response.
    Our views.py checks this and routes the
    conversation to Kapso's human inbox.

    Example:
        response = "Let me connect you...\\nHANDOFF_REQUESTED"
        is_handoff_requested(response) → True
    """
    return "HANDOFF_REQUESTED" in response_text


def clean_response(response_text: str) -> str:
    """
    Removes system tags from Gemini's response
    before sending it to the customer.

    The customer should never see:
        SHOW_IMAGES:P001
        HANDOFF_REQUESTED

    These are internal signals for our backend only.

    Example:
        Input:  "Here is your product!\\nSHOW_IMAGES:P001"
        Output: "Here is your product!"
    """
    lines = []
    for line in response_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("SHOW_IMAGES:"):
            continue
        if stripped == "HANDOFF_REQUESTED":
            continue
        lines.append(line)

    return "\n".join(lines).strip()