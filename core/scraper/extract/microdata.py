from core.scraper.extract.prices import parse_price


def extract(soup, base_url=""):
    products = []
    for scope in soup.find_all(attrs={"itemtype": True}):
        itemtype = str(scope.get("itemtype", "")).lower().rstrip("/")
        if not itemtype.endswith("/product"):
            continue

        name = _prop_value(scope, "name")
        if not name:
            continue

        products.append(
            {
                "id": _prop_value(scope, "sku") or _prop_value(scope, "productID"),
                "name": name,
                "url": _prop_value(scope, "url"),
                "price": parse_price(_prop_value(scope, "price") or _prop_value(scope, "lowPrice")),
                "currency": _prop_value(scope, "priceCurrency"),
                "description": _prop_value(scope, "description"),
                "image_urls": _prop_images(scope),
                "availability": _availability(_prop_value(scope, "availability")),
            }
        )
    return products


def _prop_value(scope, prop):
    element = scope.find(attrs={"itemprop": prop})
    if element is None:
        return ""
    for attribute in ("content", "href", "src", "data-src"):
        value = element.get(attribute)
        if value:
            return str(value).strip()
    return element.get_text(strip=True)


def _prop_images(scope):
    images = []
    for element in scope.find_all(attrs={"itemprop": "image"}):
        url = element.get("content") or element.get("src") or element.get("href")
        if url and url not in images:
            images.append(str(url).strip())
    return images


def _availability(value):
    text = str(value or "").lower()
    if "instock" in text:
        return "available"
    if "outofstock" in text or "soldout" in text:
        return "out_of_stock"
    return ""
