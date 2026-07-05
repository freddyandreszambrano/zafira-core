UPPER_BODY = "upper_body"
LOWER_BODY = "lower_body"
DRESS = "dress"

_CATEGORY_KEYWORDS = (
    (DRESS, ("vestido", "dress", "enterizo", "jumpsuit", "overol")),
    (
        LOWER_BODY,
        (
            "pantalon",
            "pantalón",
            "jean",
            "short",
            "falda",
            "legging",
            "jogger",
            "bermuda",
            "trouser",
            "skirt",
        ),
    ),
)


def garment_type_for_category(category):
    normalized = (category or "").strip().lower()
    for garment_type, keywords in _CATEGORY_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return garment_type
    return UPPER_BODY
