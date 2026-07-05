import re
from urllib.parse import urljoin

from core.scraper.extract.prices import parse_price

MIN_GROUP_SIZE = 3
MAX_CARD_TEXT = 400

PRICE_HINT_RE = re.compile(
    r"(?:[$€£]\s*\d)|(?:\d+[.,]\d{2}\s*(?:USD|EUR|\$))|(?:(?:USD|EUR|S/)\s*\d)", re.I
)
PRICE_TEXT_RE = re.compile(
    r"(?:[$€£]|USD|EUR|S/)\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?"
    r"|\d{1,3}(?:[.,]\d{3})*[.,]\d{2}(?!\d)",
    re.I,
)


def extract(soup, base_url=""):
    groups = {}
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        card = _card_root(anchor)
        if card is None:
            continue
        groups.setdefault(_signature(card), {})[id(card)] = (card, anchor)

    products = []
    seen_urls = set()
    for group in groups.values():
        if len(group) < MIN_GROUP_SIZE:
            continue
        for card, anchor in group.values():
            product = _product_from_card(card, anchor, base_url)
            if not product or product["url"] in seen_urls:
                continue
            seen_urls.add(product["url"])
            products.append(product)
    return products


def _card_root(anchor):
    node = anchor
    for _ in range(5):
        if node is None or node.name in ("body", "html"):
            return None
        text = node.get_text(" ", strip=True)
        if node.find("img") and PRICE_HINT_RE.search(text or ""):
            return node if len(text) <= MAX_CARD_TEXT else None
        node = node.parent
    return None


def _signature(card):
    parent = card.parent
    return (
        card.name,
        tuple(sorted(card.get("class") or [])),
        parent.name if parent else "",
        tuple(sorted(parent.get("class") or [])) if parent else (),
    )


def _product_from_card(card, anchor, base_url):
    name = _card_name(card, anchor)
    price, price_old = _card_prices(card)
    if not name or price is None:
        return None

    return {
        "name": name,
        "url": urljoin(base_url, anchor["href"]),
        "price": price,
        "price_old": price_old,
        "image_urls": [image for image in (_card_image(card),) if image],
    }


def _card_name(card, anchor):
    for value in (anchor.get("title"), anchor.get("aria-label")):
        if value and value.strip():
            return value.strip()

    image = card.find("img")
    if image is not None:
        alt = (image.get("alt") or "").strip()
        if len(alt) > 3:
            return alt

    heading = card.find(["h2", "h3", "h4", "h5"])
    if heading is not None:
        text = heading.get_text(strip=True)
        if text:
            return text

    candidates = [
        text.strip()
        for text in card.stripped_strings
        if len(text.strip()) > 5 and not PRICE_TEXT_RE.fullmatch(text.strip())
    ]
    return candidates[0][:150] if candidates else ""


def _card_prices(card):
    struck = card.find(["s", "del", "strike"])
    price_old = parse_price(struck.get_text(strip=True)) if struck else None

    values = []
    for match in PRICE_TEXT_RE.finditer(card.get_text(" ", strip=True)):
        value = parse_price(match.group(0))
        if value and value > 0 and value not in values:
            values.append(value)

    if not values:
        return None, price_old
    if price_old is not None:
        remaining = [value for value in values if value != price_old]
        return (remaining[0] if remaining else values[0]), price_old
    if len(values) >= 2:
        return min(values), max(values)
    return values[0], price_old


def _card_image(card):
    image = card.find("img")
    if image is None:
        return ""
    for attribute in ("data-src", "data-original", "data-lazy-src", "src"):
        value = image.get(attribute)
        if value and not str(value).startswith("data:"):
            return str(value).strip()
    srcset = image.get("srcset") or image.get("data-srcset")
    if srcset:
        return srcset.split(",")[0].strip().split(" ")[0]
    return ""
