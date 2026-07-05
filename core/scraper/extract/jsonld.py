import json

from core.scraper.extract.prices import parse_price

PRODUCT_TYPES = {"product", "individualproduct", "productmodel"}


def extract(soup, base_url=""):
    products = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        payload = _load_json(script.string or script.get_text())
        if payload is None:
            continue
        for node in _walk(payload):
            types = _types(node)
            if types & PRODUCT_TYPES:
                product = _product_from_node(node)
                if product:
                    products.append(product)
            elif "itemlist" in types:
                products.extend(_products_from_itemlist(node))
    return products


def _load_json(text):
    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _walk(payload):
    stack = [payload]
    while stack:
        node = stack.pop()
        if isinstance(node, list):
            stack.extend(node)
        elif isinstance(node, dict):
            yield node
            for key in ("@graph", "mainEntity", "hasVariant"):
                value = node.get(key)
                if value:
                    stack.append(value)


def _types(node):
    raw = node.get("@type") or ""
    if isinstance(raw, list):
        return {str(item).lower() for item in raw}
    return {str(raw).lower()}


def _products_from_itemlist(node):
    products = []
    for element in _as_list(node.get("itemListElement")):
        if not isinstance(element, dict):
            continue
        item = element.get("item") if isinstance(element.get("item"), dict) else element
        if _types(item) & PRODUCT_TYPES:
            product = _product_from_node(item)
        else:
            url = item.get("url") or element.get("url")
            if not url and isinstance(element.get("item"), str):
                url = element["item"]
            name = item.get("name") or element.get("name")
            product = {"name": name, "url": url} if url and name else None
        if product:
            products.append(product)
    return products


def _product_from_node(node):
    name = _clean(node.get("name"))
    if not name:
        return None

    offer = _first_offer(node.get("offers"))
    return {
        "id": _clean(node.get("sku") or node.get("productID") or node.get("mpn")),
        "name": name,
        "url": _clean(node.get("url") or node.get("@id")),
        "price": parse_price(offer.get("price") or offer.get("lowPrice")),
        "price_old": None,
        "currency": _clean(offer.get("priceCurrency")),
        "description": _clean(node.get("description")),
        "image_urls": _images(node.get("image")),
        "colors": [color for color in (_clean(node.get("color")),) if color],
        "category": _clean(node.get("category")),
        "availability": _availability(offer.get("availability")),
    }


def _first_offer(offers):
    for offer in _as_list(offers):
        if isinstance(offer, dict):
            nested = offer.get("offers")
            if nested and not offer.get("price") and not offer.get("lowPrice"):
                inner = _first_offer(nested)
                if inner:
                    return inner
            return offer
    return {}


def _availability(value):
    text = str(value or "").lower()
    if "instock" in text or "limitedavailability" in text:
        return "available"
    if "outofstock" in text or "soldout" in text or "discontinued" in text:
        return "out_of_stock"
    return ""


def _images(value):
    images = []
    for item in _as_list(value):
        if isinstance(item, str):
            images.append(item)
        elif isinstance(item, dict):
            url = item.get("url") or item.get("contentUrl")
            if url:
                images.append(url)
    return images


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _clean(value):
    if isinstance(value, (int, float)):
        return str(value)
    if not isinstance(value, str):
        return ""
    return value.strip()
