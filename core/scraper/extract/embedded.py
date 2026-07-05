import json

from core.scraper.extract.prices import parse_price

MAX_PRODUCTS = 60
MAX_NODES = 20000

STATE_MARKERS = ("__INITIAL_STATE__", "__PRELOADED_STATE__", "__STATE__", "__NUXT__")
NAME_KEYS = ("name", "title", "productName", "product_name", "displayName")
PRICE_KEYS = (
    "price",
    "salePrice",
    "sale_price",
    "currentPrice",
    "current_price",
    "finalPrice",
    "final_price",
    "sellingPrice",
    "bestPrice",
)
OLD_PRICE_KEYS = (
    "listPrice",
    "list_price",
    "originalPrice",
    "original_price",
    "compareAtPrice",
    "compare_at_price",
    "regularPrice",
    "priceWithoutDiscount",
)
IMAGE_KEYS = ("image", "imageUrl", "image_url", "img", "thumbnail", "featuredImage", "mainImage")
URL_KEYS = ("url", "link", "productUrl", "product_url", "canonicalUrl", "shareUrl")


def extract(soup, base_url=""):
    products = []
    seen = set()
    for blob in _json_blobs(soup):
        for node in _walk(blob):
            product = _as_product(node)
            if not product:
                continue
            key = product.get("url") or product["name"].lower()
            if key in seen:
                continue
            seen.add(key)
            products.append(product)
            if len(products) >= MAX_PRODUCTS:
                return products
    return products


def _json_blobs(soup):
    blobs = []
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data:
        blobs.append(_load(next_data.string or ""))

    for script in soup.find_all("script"):
        text = script.string or ""
        if not text:
            continue
        for marker in STATE_MARKERS:
            if marker in text:
                blobs.append(_load(_json_after(text, marker)))
                break
    return [blob for blob in blobs if blob is not None]


def _load(text):
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def _json_after(text, marker):
    start = text.find(marker)
    if start == -1:
        return ""
    brace = text.find("{", start)
    if brace == -1:
        return ""

    depth = 0
    in_string = False
    escaped = False
    for index in range(brace, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[brace : index + 1]
    return ""


def _walk(blob):
    stack = [blob]
    visited = 0
    while stack and visited < MAX_NODES:
        node = stack.pop()
        visited += 1
        if isinstance(node, dict):
            yield node
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)


def _as_product(node):
    name = _first_str(node, NAME_KEYS)
    if not name or not 3 <= len(name) <= 200:
        return None

    price = _first_price(node, PRICE_KEYS)
    if price is None or price <= 0:
        return None

    return {
        "name": name,
        "price": price,
        "price_old": _first_price(node, OLD_PRICE_KEYS),
        "url": _first_str(node, URL_KEYS),
        "image_urls": [image for image in (_image_of(node),) if image],
        "id": _first_str(node, ("sku", "productId", "product_id", "itemId")),
    }


def _first_str(node, keys):
    for key in keys:
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _first_price(node, keys):
    for key in keys:
        value = node.get(key)
        if isinstance(value, (int, float, str)) and str(value).strip():
            price = parse_price(value)
            if price is not None:
                return price
    return None


def _image_of(node):
    for key in IMAGE_KEYS:
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            nested = value.get("url") or value.get("src")
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
        if isinstance(value, list) and value and isinstance(value[0], str):
            return value[0].strip()
    return ""
