from core.scraper.extract.prices import detect_currency, parse_price


def extract(soup, base_url=""):
    meta = {}
    images = []
    for tag in soup.find_all("meta"):
        key = tag.get("property") or tag.get("name") or ""
        content = tag.get("content")
        if not key or not content:
            continue
        key = key.lower()
        if key == "og:image":
            images.append(content.strip())
        meta.setdefault(key, content.strip())

    price = parse_price(
        meta.get("product:price:amount")
        or meta.get("og:price:amount")
        or meta.get("product:price")
        or meta.get("twitter:data1")
    )
    og_type = meta.get("og:type", "")
    if "product" not in og_type and price is None:
        return []

    name = meta.get("og:title") or meta.get("twitter:title")
    if not name:
        return []

    return [
        {
            "name": name,
            "url": meta.get("og:url"),
            "price": price,
            "currency": meta.get("product:price:currency")
            or meta.get("og:price:currency")
            or detect_currency(meta.get("twitter:data1")),
            "description": meta.get("og:description") or meta.get("description"),
            "image_urls": images,
            "availability": _availability(
                meta.get("product:availability") or meta.get("og:availability")
            ),
        }
    ]


def _availability(value):
    text = str(value or "").lower()
    if "instock" in text or text == "available":
        return "available"
    if "oos" in text or "outofstock" in text or "out of stock" in text:
        return "out_of_stock"
    return ""
