def get_reviews_by_product(product_type: str):
    """
    Replace this with real DB later
    """

    MOCK_REVIEWS = {
        "sofa": [
            {
                "review": "Using it daily for 6 months, still very comfortable.",
                "tags": ["lifestyle", "family"]
            },
            {
                "review": "Good back support, helpful for long sitting.",
                "tags": ["health"]
            }
        ],
        "mattress": [
            {
                "review": "My back pain reduced after using this.",
                "tags": ["health"]
            },
            {
                "review": "Feels premium and very soft.",
                "tags": ["lifestyle"]
            }
        ]
    }

    return MOCK_REVIEWS.get(product_type, [])