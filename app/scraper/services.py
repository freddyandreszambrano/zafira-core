from urllib.parse import urlparse

from app.scraper import parsers
from app.scraper.adapters import ADAPTER_MAP


MAX_PRODUCTS_LIMIT = 50


def normalize_max_products(value, default=10):
    try:
        max_products = int(value or default)
    except (TypeError, ValueError):
        raise ValueError('El maximo de productos debe ser un numero entero.')

    if max_products < 1:
        raise ValueError('El maximo de productos debe ser mayor a 0.')
    if max_products > MAX_PRODUCTS_LIMIT:
        raise ValueError(f'El maximo permitido es {MAX_PRODUCTS_LIMIT}.')
    return max_products


def scan_url(store, source_url, max_products=10):
    source_url = (source_url or '').strip()
    try:
        adapter = _get_adapter(store)
    except ValueError as e:
        return _error_response(store, source_url, str(e))

    if not source_url:
        return _error_response(store, source_url, 'Ingrese una URL para escanear.')

    if store == 'modarm' and not _is_modarm_url(source_url):
        return _error_response(store, source_url, 'La URL debe pertenecer a modarm.com.')

    try:
        max_products = normalize_max_products(max_products)
    except ValueError as e:
        return _error_response(store, source_url, str(e))

    if '/p/' in source_url:
        product = adapter.parse_product(source_url)
        products = [product] if product else []
        return _success_response(store, source_url, 'product', products, [])

    category = {
        'name': 'URL personalizada',
        'path': urlparse(source_url).path,
        'url': source_url,
    }
    return _scan_category(adapter, store, source_url, category, max_products)


def scan_store(store, max_products=None):
    adapter = _get_adapter(store)
    products = {}
    errors = []
    categories = adapter.get_categories()

    for category in categories:
        category_result = _scan_category(adapter, store, category['url'], category, max_products, as_partial=True)
        for product in category_result['products']:
            product_key = product.get('id') or product.get('url')
            if product_key:
                products[product_key] = product
        errors.extend(category_result['errors'])
        if max_products and len(products) >= max_products:
            break

    product_list = list(products.values())
    return {
        'success': True,
        'metadata': {
            'store': store,
            'source_url': None,
            'mode': 'store',
            'scraped_at': parsers.now_iso(),
            'total_products': len(product_list),
            'total_categories': len(categories),
            'total_errors': len(errors),
        },
        'products': product_list,
        'errors': errors,
    }


def _get_adapter(store):
    if store not in ADAPTER_MAP:
        available = ', '.join(ADAPTER_MAP.keys())
        raise ValueError(f"Adaptador '{store}' no encontrado. Disponibles: {available}")
    return ADAPTER_MAP[store]()


def _scan_category(adapter, store, source_url, category, max_products, as_partial=False):
    products = {}
    errors = []

    try:
        category_products = adapter.scrape_category(category)
    except Exception as e:
        errors.append(f"{category.get('name', source_url)}: {e}")
        category_products = []

    for product_link in category_products:
        if max_products and len(products) >= max_products:
            break
        try:
            product = adapter.parse_product(product_link['url'])
            product_key = product.get('id') or product_link.get('id') or product_link.get('url')
            if product_key:
                products[product_key] = product
        except Exception as e:
            errors.append(f"{product_link.get('id', 'unknown')}: {e}")

    product_list = list(products.values())
    if as_partial:
        return {'products': product_list, 'errors': errors}
    return _success_response(store, source_url, 'category', product_list, errors)


def _success_response(store, source_url, mode, products, errors):
    return {
        'success': True,
        'metadata': {
            'store': store,
            'source_url': source_url,
            'mode': mode,
            'scraped_at': parsers.now_iso(),
            'total_products': len(products),
            'total_errors': len(errors),
        },
        'products': products,
        'errors': errors,
    }


def _error_response(store, source_url, message):
    return {
        'success': False,
        'error': message,
        'metadata': {
            'store': store,
            'source_url': source_url,
            'mode': None,
            'scraped_at': parsers.now_iso(),
            'total_products': 0,
            'total_errors': 1,
        },
        'products': [],
        'errors': [message],
    }


def _is_modarm_url(url):
    hostname = urlparse(url).hostname or ''
    return hostname == 'modarm.com' or hostname.endswith('.modarm.com')
