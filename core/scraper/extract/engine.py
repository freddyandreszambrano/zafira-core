import hashlib
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from core.scraper import parsers
from core.scraper.extract import embedded, heuristic, jsonld, microdata, opengraph
from core.scraper.extract.prices import parse_price

LISTING_STRATEGIES = (
    ("json-ld", jsonld.extract),
    ("microdata", microdata.extract),
    ("embedded-json", embedded.extract),
    ("heuristic", heuristic.extract),
)

PRODUCT_STRATEGIES = (
    ("json-ld", jsonld.extract),
    ("opengraph", opengraph.extract),
    ("microdata", microdata.extract),
    ("embedded-json", embedded.extract),
    ("heuristic", heuristic.extract),
)

ENOUGH_PRODUCTS = 40


def soup_of(html):
    return BeautifulSoup(html, "html.parser")


def extract_products(html, url):
    soup = soup_of(html)
    merged, strategies = {}, []

    for name, strategy in LISTING_STRATEGIES:
        added = False
        for product in _safe_run(strategy, soup, url):
            product = finalize(product, url)
            if not product:
                continue
            key = product.get("url") or product["name"].lower()
            if key in merged:
                _fill_missing(merged[key], product)
            else:
                merged[key] = product
                added = True
        if added:
            strategies.append(name)
        complete = [p for p in merged.values() if p.get("price") is not None]
        if len(complete) >= ENOUGH_PRODUCTS:
            break

    return list(merged.values()), strategies


def extract_product(html, url):
    soup = soup_of(html)
    result, strategies = {}, []

    for name, strategy in PRODUCT_STRATEGIES:
        candidates = _safe_run(strategy, soup, url)
        candidate = _closest_to_url(candidates, url)
        if candidate is None:
            continue
        candidate = finalize(candidate, url)
        if not candidate:
            continue
        if not result:
            result = candidate
        else:
            _fill_missing(result, candidate)
        strategies.append(name)
        if (
            result.get("price") is not None
            and result.get("image_urls")
            and result.get("description")
        ):
            break

    if result:
        result["url"] = result.get("url") or url
        result["id"] = result.get("id") or slug_id(result["url"])
    return result, strategies


def finalize(product, base_url):
    name = _clean_text(product.get("name"))
    if not name or len(name) < 2:
        return None

    url = product.get("url")
    if url:
        url = urljoin(base_url, str(url).strip())
        if urlparse(url).scheme not in ("http", "https"):
            url = None

    images = []
    for image in product.get("image_urls") or []:
        if not image:
            continue
        image = urljoin(base_url, str(image).strip())
        if image.startswith("http") and image not in images:
            images.append(image)

    price = parse_price(product.get("price"))
    price_old = parse_price(product.get("price_old"))
    if price is not None and price_old is not None and price_old <= price:
        price_old = None

    currency = str(product.get("currency") or "").strip().upper()

    return {
        "id": _clean_text(product.get("id")) or None,
        "name": name[:300],
        "category": _clean_text(product.get("category")),
        "url": url,
        "price": price,
        "price_old": price_old,
        "currency": currency[:3] if currency else "USD",
        "sizes": _str_list(product.get("sizes")),
        "colors": _str_list(product.get("colors")),
        "description": _clean_text(product.get("description"))[:2000],
        "image_urls": images[:10],
        "availability": product.get("availability") or "unknown",
        "extracted_at": product.get("extracted_at") or parsers.now_iso(),
    }


def slug_id(url):
    path = urlparse(url).path.strip("/")
    path = re.sub(r"\.(html?|php|aspx?)$", "", path)
    segment = re.sub(r"[^A-Za-z0-9]+", "-", path).strip("-")[:80]
    if len(segment) >= 3:
        return segment
    return hashlib.md5(url.encode()).hexdigest()[:12]


def looks_js_rendered(html):
    soup = soup_of(html)
    return len(soup.find_all("a", href=True)) < 10


def _safe_run(strategy, soup, url):
    try:
        return strategy(soup, url) or []
    except Exception:
        return []


def _closest_to_url(candidates, url):
    if not candidates:
        return None
    target_path = urlparse(url).path.rstrip("/")
    for candidate in candidates:
        candidate_url = str(candidate.get("url") or "")
        if candidate_url and urlparse(candidate_url).path.rstrip("/") == target_path:
            return candidate
    return candidates[0]


def _fill_missing(target, source):
    for key, value in source.items():
        current = target.get(key)
        if current in (None, "", [], "unknown", "USD") and value not in (None, "", []):
            target[key] = value


def _clean_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _str_list(value, limit=20):
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if isinstance(item, (str, int, float))][:limit]
