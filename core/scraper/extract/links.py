from urllib.parse import urljoin, urlparse

PRODUCT_PATTERNS = (
    "/p/",
    "/product/",
    "/products/",
    "/producto/",
    "/productos/",
    "/item/",
    "/prod/",
    "/dp/",
    "-p-",
    "/pd/",
)

LISTING_PATTERNS = (
    "/c/",
    "/category/",
    "/categories/",
    "/categoria/",
    "/collections/",
    "/collection/",
    "/catalogo/",
    "/catalog/",
    "/shop/",
    "/tienda/",
    "/coleccion",
    "/mujer",
    "/hombre",
    "/women",
    "/men",
    "/dama",
    "/caballero",
    "/moda-",
    "/ropa",
)


def product_links(soup, base_url):
    host = _host(base_url)
    links, seen = [], set()
    for anchor in soup.find_all("a", href=True):
        full_url = urljoin(base_url, anchor["href"])
        parsed = urlparse(full_url)
        if _host(full_url) != host:
            continue
        path = parsed.path.lower()
        if not any(pattern in path for pattern in PRODUCT_PATTERNS):
            continue
        clean = full_url.split("#")[0]
        if clean in seen or _is_listing_only(path):
            continue
        seen.add(clean)
        links.append({"id": None, "name": _anchor_name(anchor), "url": clean})
    return links


def listing_links(soup, base_url, limit=8):
    host = _host(base_url)
    base_path = urlparse(base_url).path.rstrip("/")
    urls, seen = [], set()
    for anchor in soup.find_all("a", href=True):
        full_url = urljoin(base_url, anchor["href"]).split("#")[0]
        parsed = urlparse(full_url)
        if _host(full_url) != host:
            continue
        path = parsed.path.lower().rstrip("/")
        if not path or path == base_path:
            continue
        if any(pattern in path for pattern in PRODUCT_PATTERNS):
            continue
        if not any(pattern in path for pattern in LISTING_PATTERNS):
            continue
        if full_url in seen:
            continue
        seen.add(full_url)
        urls.append(full_url)
        if len(urls) >= limit:
            break
    return urls


def _is_listing_only(path):
    # /products/ o /productos/ sin slug es un índice, no un producto
    trimmed = path.rstrip("/")
    return trimmed.endswith(("/products", "/productos", "/product", "/producto"))


def _anchor_name(anchor):
    for value in (anchor.get("title"), anchor.get("aria-label"), anchor.get("data-product-name")):
        if value and value.strip():
            return value.strip()[:150]
    image = anchor.find("img")
    if image is not None:
        alt = (image.get("alt") or "").strip()
        if alt:
            return alt[:150]
    return anchor.get_text(strip=True)[:150]


def _host(url):
    host = urlparse(url).hostname or ""
    return host.lower().removeprefix("www.")
