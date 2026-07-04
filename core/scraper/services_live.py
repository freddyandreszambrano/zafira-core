"""Consulta en vivo de un producto contra la página oficial de la tienda.

A diferencia del scrape completo (que usa Playwright y verifica stock por
talla), esta consulta es ligera: un solo GET a la página del producto para
leer el precio y las tallas tal como los muestra el sitio oficial en este
momento. Pensada para ejecutarse al abrir el detalle de una prenda.
"""

import logging

from django.core.cache import cache

import requests
from bs4 import BeautifulSoup

from core.scraper.adapters.etafashion import EtafashionAdapter
from core.scraper.adapters.modarm import ModarmAdapter

logger = logging.getLogger(__name__)

_LIVE_CACHE_TTL = 300  # 5 minutos: evita golpear la tienda si reabren el detalle
_TIMEOUT = 10

_ADAPTER_CLASSES = {
    "modarm": ModarmAdapter,
    "etafashion": EtafashionAdapter,
}

_adapters: dict = {}


def _get_adapter(store: str):
    """Adapter singleton por tienda (solo se usan sus métodos de parseo)."""
    if store not in _adapters:
        adapter_cls = _ADAPTER_CLASSES.get(store, ModarmAdapter)
        _adapters[store] = adapter_cls()
    return _adapters[store]


def fetch_live_product_data(product) -> dict | None:
    """Lee precio y tallas actuales desde la página oficial del producto.

    Retorna dict con price, price_old, sizes y availability, o None si la
    página no respondió. El resultado se cachea 5 minutos por producto.
    """
    cache_key = f"live_product_{product.id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    adapter = _get_adapter(product.store)

    try:
        response = requests.get(
            product.url,
            headers={"User-Agent": adapter.USER_AGENT},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.warning("Live fetch fallo para producto %s (%s)", product.id, product.url)
        return None

    soup = BeautifulSoup(response.content, "html.parser")

    # Tallas tal como aparecen en el selector del sitio (sin filtrar stock,
    # que requiere navegador y tarda demasiado para una consulta en vivo)
    size_options = adapter._extract_size_options(soup)
    sizes = [opt["label"] for opt in size_options]

    data = {
        "price": adapter._extract_price(soup),
        "price_old": adapter._extract_price_old(soup),
        "sizes": sizes,
        "availability": adapter._extract_availability(soup),
    }

    cache.set(cache_key, data, _LIVE_CACHE_TTL)
    return data


def refresh_product_from_live(product) -> bool:
    """Actualiza el registro del producto con los datos en vivo.

    Retorna True si hubo datos frescos y se actualizó.
    """
    data = fetch_live_product_data(product)
    if not data:
        return False

    updates = []
    if data["price"] is not None and float(product.price) != data["price"]:
        product.price = data["price"]
        updates.append("price")
    if data["price_old"] is not None:
        product.price_old = data["price_old"]
        updates.append("price_old")
    if data["sizes"] and data["sizes"] != product.sizes:
        product.sizes = data["sizes"]
        updates.append("sizes")
    if data["availability"] != "unknown" and data["availability"] != product.availability:
        product.availability = data["availability"]
        updates.append("availability")

    if updates:
        product.save(update_fields=updates + ["updated_at"])
    return True
