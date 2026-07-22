import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from django.conf import settings
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now

from core.scraper import parsers
from core.scraper.adapters import ADAPTER_MAP, GENERIC_STORE
from core.scraper.models import Product, ScraperSource

MAX_PRODUCTS_LIMIT = 50
PRICE_MAX = Decimal("99999999.99")  # coincide con DecimalField(max_digits=10, decimal_places=2)

# 'woman' primero + límite de palabra: evita que 'men' matchee 'women' y
# 'male' matchee 'female'.
GENDER_KEYWORDS = {
    "woman": ("mujer", "dama", "women", "female", "femenino"),
    "man": ("hombre", "caballero", "men", "male", "masculino"),
}


def _cap_for_lite_mode(max_products):
    """En modo ligero (SCRAPER_USE_BROWSER=false) cada prenda es una petición
    HTTP secuencial, así que un número alto se pasaría del límite de 30s del
    servidor gratis. Se recorta el total para que el escaneo siempre termine."""
    if getattr(settings, "SCRAPER_USE_BROWSER", True):
        return max_products
    lite_max = int(getattr(settings, "SCRAPER_LITE_MAX_PRODUCTS", 10))
    return min(max_products, lite_max)


def normalize_max_products(value, default=10):
    try:
        max_products = int(value or default)
    except (TypeError, ValueError):
        raise ValueError("El maximo de productos debe ser un numero entero.")

    if max_products < 1:
        raise ValueError("El maximo de productos debe ser mayor a 0.")
    if max_products > MAX_PRODUCTS_LIMIT:
        raise ValueError(f"El maximo permitido es {MAX_PRODUCTS_LIMIT}.")
    return max_products


def scan_url(store, source_url, max_products=10, persist=True):
    source_url = (source_url or "").strip()
    try:
        adapter = _get_adapter(store)
    except ValueError as e:
        return _error_response(store, source_url, str(e))

    if not source_url:
        return _error_response(store, source_url, "Ingrese una URL para escanear.")

    if not adapter.supports_url(source_url):
        return _error_response(
            store,
            source_url,
            f"La URL debe pertenecer a {_supported_domains_label(adapter)}.",
        )

    try:
        max_products = normalize_max_products(max_products)
    except ValueError as e:
        return _error_response(store, source_url, str(e))

    max_products = _cap_for_lite_mode(max_products)
    store_name = _store_label(store, source_url)

    try:
        if adapter.is_product_url(source_url):
            return _scan_product(adapter, store_name, source_url, persist)

        categories = adapter.get_categories()
        if categories and not urlparse(source_url).path.strip("/"):
            return _scan_root(adapter, store_name, source_url, categories, max_products, persist)

        category = {
            "name": "URL personalizada",
            "path": urlparse(source_url).path,
            "url": source_url,
        }
        return _scan_category(adapter, store_name, source_url, category, max_products, persist)
    finally:
        _close_adapter(adapter)


def scan_auto_url(source_url, max_products=10, persist=True):
    source_url = (source_url or "").strip()
    if not source_url:
        return _error_response("", source_url, "Ingrese una URL para escanear.")

    try:
        store = infer_store_from_url(source_url)
    except ValueError as e:
        return _error_response("", source_url, str(e))
    return scan_url(store, source_url, max_products=max_products, persist=persist)


def scan_store(store, max_products=None):
    adapter = _get_adapter(store)
    products = {}
    errors = []
    categories = adapter.get_categories()

    if not categories:
        _close_adapter(adapter)
        raise ValueError(
            f"El adaptador '{store}' no define categorias; escanee una URL especifica."
        )

    per_category_limit = None
    if max_products:
        per_category_limit = max(1, max_products // len(categories))

    try:
        for category in categories:
            category_result = _scan_category(
                adapter, store, category["url"], category, per_category_limit, as_partial=True
            )
            for product in category_result["products"]:
                product_key = product.get("id") or product.get("url")
                if product_key:
                    products[product_key] = product
            errors.extend(category_result["errors"])
    finally:
        _close_adapter(adapter)

    product_list = list(products.values())
    return {
        "success": True,
        "metadata": {
            "store": store,
            "source_url": None,
            "mode": "store",
            "scraped_at": parsers.now_iso(),
            "total_products": len(product_list),
            "total_categories": len(categories),
            "total_errors": len(errors),
        },
        "products": product_list,
        "errors": errors,
    }


def scan_saved_sources(max_products=10, persist=True):
    sources = ScraperSource.objects.all().order_by("name")
    products = {}
    errors = []
    results = []

    for source in sources:
        result = scan_auto_url(source.url, max_products=max_products, persist=persist)
        results.append(
            {
                "source": source.to_json(),
                "success": result["success"],
                "total_products": result["metadata"]["total_products"],
                "errors": result.get("errors", []),
            }
        )
        for product in result.get("products", []):
            product_key = product.get("id") or product.get("url")
            if product_key:
                products[product_key] = product
        errors.extend(result.get("errors", []))

    product_list = list(products.values())
    return {
        "success": True,
        "metadata": {
            "store": None,
            "source_url": None,
            "mode": "saved_sources",
            "scraped_at": parsers.now_iso(),
            "total_sources": sources.count(),
            "total_products": len(product_list),
            "total_errors": len(errors),
        },
        "products": product_list,
        "errors": errors,
        "results": results,
    }


def save_products(store, products):
    store = (store or "").strip()
    if not store:
        raise ValueError("Falta la tienda de origen de los productos.")
    if not isinstance(products, list) or not products:
        raise ValueError("No hay productos para guardar.")
    if len(products) > MAX_PRODUCTS_LIMIT * 2:
        raise ValueError("Demasiados productos en una sola operacion.")
    if not all(isinstance(product, dict) for product in products):
        raise ValueError("Formato de productos invalido.")
    return _persist_products(store, products)


def infer_store_from_url(source_url):
    source_url = (source_url or "").strip()
    for store, adapter_cls in ADAPTER_MAP.items():
        if store == GENERIC_STORE:
            continue
        if adapter_cls.supports_url(source_url):
            return store

    if ADAPTER_MAP[GENERIC_STORE].supports_url(source_url):
        return GENERIC_STORE
    raise ValueError("Ingrese una URL valida (http/https).")


def _store_label(store, source_url):
    if store != GENERIC_STORE:
        return store
    hostname = urlparse(source_url).hostname or GENERIC_STORE
    return hostname.lower().removeprefix("www.")


def _scan_product(adapter, store_name, source_url, persist):
    try:
        product = adapter.parse_product(source_url)
    except Exception as e:
        return _error_response(store_name, source_url, _friendly_error(e))
    if not product or not product.get("id") or not product.get("name"):
        return _error_response(
            store_name, source_url, "No se pudo extraer un producto valido de esta URL."
        )
    if persist:
        _persist_products(store_name, [product])
    return _success_response(adapter, store_name, source_url, "product", [product], [], persist)


def _scan_root(adapter, store_name, source_url, categories, max_products, persist):
    links = []
    seen = set()
    errors = []

    # Recorre categorías solo hasta juntar suficientes candidatos: escanear
    # las 9 categorías con navegador tomaría minutos en la vista.
    for category in categories:
        try:
            found = adapter.scrape_category(category)
        except Exception as e:
            errors.append(f"{category.get('name', category['url'])}: {_friendly_error(e)}")
            continue
        for link in found:
            key = link.get("id") or link.get("url")
            if key and key not in seen:
                seen.add(key)
                links.append(link)
        if len(links) >= max_products * 3:
            break

    products, parse_errors = _parse_links(adapter, links, max_products)
    errors.extend(parse_errors)

    if persist:
        _persist_products(store_name, products)
    return _success_response(adapter, store_name, source_url, "store", products, errors, persist)


def _scan_category(
    adapter, store_name, source_url, category, max_products, persist=True, as_partial=False
):
    errors = []

    try:
        category_products = adapter.scrape_category(category)
    except Exception as e:
        errors.append(f"{category.get('name', source_url)}: {_friendly_error(e)}")
        category_products = []

    products, parse_errors = _parse_links(adapter, category_products, max_products)
    errors.extend(parse_errors)

    if persist:
        _persist_products(store_name, products)

    if as_partial:
        return {"products": products, "errors": errors}
    return _success_response(adapter, store_name, source_url, "category", products, errors, persist)


def _parse_links(adapter, links, max_products):
    products = {}
    errors = []

    for product_link in _spread_sample(links, max_products):
        try:
            product = adapter.parse_product(product_link["url"])
        except Exception as e:
            errors.append(
                f"{product_link.get('name') or product_link['url']}: {_friendly_error(e)}"
            )
            continue

        if not product or not product.get("id") or not product.get("name"):
            errors.append(f"{product_link['url']}: sin datos de producto")
            continue
        products[product["id"]] = product

    return list(products.values()), errors


def _spread_sample(items, max_count):
    """Selecciona `max_count` elementos repartidos a lo largo de la lista
    en vez de tomar siempre los primeros, para obtener variedad real."""
    if not max_count or len(items) <= max_count:
        return items

    step = len(items) / max_count
    indices = [int(i * step) for i in range(max_count)]
    return [items[i] for i in indices]


def _friendly_error(error):
    text = str(error)
    if "Executable doesn't exist" in text or "playwright install" in text:
        return (
            "Falta el navegador de Playwright en el servidor. "
            "Ejecuta: python -m playwright install chromium"
        )
    return text


def _close_adapter(adapter):
    close = getattr(adapter, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass


def _get_adapter(store):
    if store not in ADAPTER_MAP:
        available = ", ".join(ADAPTER_MAP.keys())
        raise ValueError(f"Adaptador '{store}' no encontrado. Disponibles: {available}")
    return ADAPTER_MAP[store]()


def _supported_domains_label(adapter):
    domains = getattr(adapter, "SUPPORTED_DOMAINS", ())
    if len(domains) == 1:
        return domains[0]
    return ", ".join(domains) or "un dominio soportado"


def _derive_gender(category, url=""):
    haystack = f"{category or ''} {url or ''}".lower()
    for gender, keywords in GENDER_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(keyword)}", haystack) for keyword in keywords):
            return gender
    return ""


# Las tiendas juntan faldas y vestidos en UNA categoría ("FALDAS Y VESTIDOS").
# El nombre del producto decide la categoría real para que la app las muestre
# separadas y el probador les dé el tratamiento correcto (vestido vs falda).
_DRESS_NAME_KEYWORDS = ("vestido", "enterizo", "jumpsuit", "overol", "conjunto", "set ")
_SKIRT_NAME_KEYWORDS = ("falda", "short", "bermuda", "pantal", "legging", "skirt")
_MIXED_CATEGORY_RE = re.compile(r"FALDAS\s+Y\s+VESTIDOS", re.IGNORECASE)


def _normalize_category(name, category):
    category = str(category or "")
    upper = category.upper()
    if "FALDA" not in upper or "VESTIDO" not in upper:
        return category

    name_l = (name or "").lower()
    is_dress = any(keyword in name_l for keyword in _DRESS_NAME_KEYWORDS)
    is_skirt = any(keyword in name_l for keyword in _SKIRT_NAME_KEYWORDS)
    # "Enterizo Short" es vestido aunque diga short; sin pistas gana vestido
    # (la categoría mixta la dominan los vestidos)
    segment = "FALDAS" if is_skirt and not is_dress else "VESTIDOS"
    return _MIXED_CATEGORY_RE.sub(segment, category)


def _coerce_price(value, default=None):
    if value in (None, ""):
        return default
    try:
        price = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        return default
    if price < 0 or price > PRICE_MAX:
        return default
    return price


def _safe_http_url(value):
    value = str(value or "").strip()
    return value if urlparse(value).scheme in ("http", "https") else ""


def _derive_base_name(name, colors):
    name = (name or "").strip()
    color = colors[0] if colors else None
    if not name or not color:
        return name

    if name.lower().endswith(color.lower()):
        return name[: -len(color)].strip()
    return name


@transaction.atomic
def _persist_products(store, products):
    created = 0
    updated = 0
    skipped = 0

    for product in products:
        product_id = str(product.get("id") or "").strip()
        name = str(product.get("name") or "").strip()
        if not product_id or not name:
            skipped += 1
            continue

        extracted_at = parse_datetime(str(product.get("extracted_at") or "")) or now()
        colors = [str(color) for color in product.get("colors") or []]

        _, was_created = Product.objects.update_or_create(
            store=store,
            id_external=product_id,
            defaults={
                "name": name,
                "base_name": _derive_base_name(name, colors),
                "category": _normalize_category(name, product.get("category")),
                "gender": _derive_gender(product.get("category"), product.get("url")),
                "url": _safe_http_url(product.get("url")),
                "price": _coerce_price(product.get("price"), default=Decimal("0")),
                "price_old": _coerce_price(product.get("price_old")),
                "currency": str(product.get("currency") or "USD"),
                "sizes": [str(size) for size in product.get("sizes") or []],
                "colors": colors,
                "description": str(product.get("description") or ""),
                "image_urls": [str(image) for image in product.get("image_urls") or []],
                "availability": str(product.get("availability") or "unknown"),
                "extracted_at": extracted_at,
            },
        )
        created += int(was_created)
        updated += int(not was_created)

    return {"created": created, "updated": updated, "skipped": skipped}


def _success_response(adapter, store_name, source_url, mode, products, errors, persist):
    return {
        "success": True,
        "metadata": {
            "store": store_name,
            "source_url": source_url,
            "mode": mode,
            "scraped_at": parsers.now_iso(),
            "total_products": len(products),
            "total_errors": len(errors),
            "strategies": list(getattr(adapter, "last_strategies", []) or []),
            "persisted": persist,
        },
        "products": products,
        "errors": errors,
    }


def _error_response(store, source_url, message):
    return {
        "success": False,
        "error": message,
        "metadata": {
            "store": store,
            "source_url": source_url,
            "mode": None,
            "scraped_at": parsers.now_iso(),
            "total_products": 0,
            "total_errors": 1,
        },
        "products": [],
        "errors": [message],
    }
