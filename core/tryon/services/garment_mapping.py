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


# Dentro de la categoría mixta "FALDAS Y VESTIDOS" (junta faldas y vestidos en
# una sola), el NOMBRE del producto desambigua el tipo real de la prenda.
_MIXED_DRESS_NAME = ("vestido", "enterizo", "jumpsuit", "overol", "conjunto", "set ")
_MIXED_LOWER_NAME = (
    "falda",
    "short",
    "bermuda",
    "pantalon",
    "pantalón",
    "jean",
    "legging",
    "culotte",
    "palazzo",
)


def garment_type_for_category(category):
    normalized = (category or "").strip().lower()
    for garment_type, keywords in _CATEGORY_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return garment_type
    return UPPER_BODY


def garment_type_for_product(name, category):
    """Tipo de prenda a partir del nombre + la categoría.

    La categoría basta para casi todo, PERO 'FALDAS Y VESTIDOS' mezcla faldas
    (lower_body) y vestidos (dress) en una sola categoría; ahí el nombre del
    producto decide. Para cualquier otra categoría se respeta exactamente el
    comportamiento anterior (sin regresión en blusas, pantalones, chaquetas…)."""
    normalized_cat = (category or "").strip().lower()
    if "falda" in normalized_cat and "vestido" in normalized_cat:
        name_l = (name or "").strip().lower()
        if any(k in name_l for k in _MIXED_DRESS_NAME):
            return DRESS
        if any(k in name_l for k in _MIXED_LOWER_NAME):
            return LOWER_BODY
        return DRESS  # sin pistas en el nombre: la categoría la dominan vestidos
    return garment_type_for_category(category)
