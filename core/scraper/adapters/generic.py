import ipaddress
import re
from typing import Dict, List
from urllib.parse import urlparse

import requests

from core.scraper import parsers
from core.scraper.adapters.browser import BrowserFetcher
from core.scraper.base import BaseAdapter
from core.scraper.extract import engine
from core.scraper.extract import links as link_discovery
from core.scraper.extract.prices import parse_price

_BLOCKED_HOSTNAMES = {"localhost", "ip6-localhost", "metadata", "metadata.google.internal"}


def _is_public_host(hostname):
    """Bloquea hosts internos para no convertir el scraper en un SSRF hacia la
    red del servidor (169.254.169.254, localhost, rangos privados)."""
    host = (hostname or "").lower().strip(".")
    if not host or host in _BLOCKED_HOSTNAMES:
        return False
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        # Dominio (no IP literal). No resolvemos DNS aqui para no volver
        # fragiles los tests ni bloquear tiendas legitimas.
        return "." in host
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


class GenericAdapter(BaseAdapter):
    """Adaptador multi-estrategia para cualquier tienda sin adaptador propio:
    JSON-LD, Shopify products.json, microdata, OpenGraph, JSON embebido y
    heurística de cards, con fallback a navegador headless para sitios SPA."""

    SUPPORTED_DOMAINS = ()
    TIMEOUT = 12
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    MIN_FULL_PRODUCTS = 3
    MAX_LISTING_CRAWL = 4
    MAX_LINKS = 60

    def __init__(self):
        self._browser = None
        self._html_cache = {}
        self._prefetched = {}
        self.last_strategies = []

    @classmethod
    def supports_url(cls, url):
        parsed = urlparse(url or "")
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False
        return _is_public_host(parsed.hostname)

    @classmethod
    def is_product_url(cls, url):
        return False

    def close(self):
        if self._browser is not None:
            self._browser.close()
            self._browser = None

    def get_categories(self) -> List[Dict]:
        return []

    def scrape_category(self, category: Dict) -> List[Dict]:
        url = category["url"]

        shopify = self._shopify_products(url)
        if shopify:
            self.last_strategies = ["shopify"]
            return self._register(shopify)

        links = self._collect(url, allow_render=True)
        if links:
            return links

        for listing_url in self._listing_urls(url):
            try:
                found = self._collect(listing_url, allow_render=False)
            except requests.RequestException:
                continue
            seen = {link["url"] for link in links}
            links.extend(link for link in found if link["url"] not in seen)
            if len(links) >= self.MAX_LINKS:
                break
        return links

    def parse_product(self, url: str) -> Dict:
        prefetched = self._prefetched.get(url)
        if prefetched and prefetched.get("price") is not None and prefetched.get("image_urls"):
            return prefetched

        try:
            html = self._fetch(url)
        except requests.RequestException:
            if prefetched:
                return prefetched
            raise
        product, _ = engine.extract_product(html, url)
        if prefetched:
            if not product:
                return prefetched
            for key, value in prefetched.items():
                if product.get(key) in (None, "", [], "unknown") and value not in (None, "", []):
                    product[key] = value
        if not product:
            raise ValueError("No se pudo extraer informacion de producto de esta pagina.")

        product["url"] = product.get("url") or url
        product["id"] = product.get("id") or engine.slug_id(product["url"])
        return product

    def _collect(self, url, allow_render):
        html = self._fetch(url)
        links = self._extract_links(html, url)
        if links:
            return links
        if allow_render and engine.looks_js_rendered(html):
            html = self._fetch_rendered(url)
            return self._extract_links(html, url)
        return []

    def _extract_links(self, html, url):
        found, list_strategies = engine.extract_products(html, url)
        complete = [p for p in found if p.get("price") is not None and p.get("url")]
        if complete:
            self.last_strategies = list_strategies
            return self._with_discovered(self._register(complete), html, url)

        single, single_strategies = engine.extract_product(html, url)
        if single and single.get("price") is not None:
            self.last_strategies = single_strategies
            single["url"] = single.get("url") or url
            return self._register([single])

        # Entradas estructuradas con URL pero sin precio (ItemList sin offers):
        # sirven como links para que parse_product las enriquezca luego.
        partial = [p for p in found if p.get("url")]
        if partial:
            self.last_strategies = list_strategies
            return self._with_discovered(self._register(partial), html, url)

        discovered = link_discovery.product_links(engine.soup_of(html), url)
        if discovered:
            self.last_strategies = ["links"]
        return discovered[: self.MAX_LINKS]

    def _with_discovered(self, registered, html, url):
        seen = {link["url"] for link in registered}
        registered.extend(
            link
            for link in link_discovery.product_links(engine.soup_of(html), url)
            if link["url"] not in seen
        )
        return registered[: self.MAX_LINKS]

    def _register(self, products):
        registered = []
        for product in products:
            url = product.get("url")
            if not url:
                continue
            product["id"] = product.get("id") or engine.slug_id(url)
            self._prefetched[url] = product
            registered.append({"id": product["id"], "name": product["name"], "url": url})
        return registered

    def _listing_urls(self, url):
        html = self._html_cache.get(url)
        if html is None:
            return []
        return link_discovery.listing_links(engine.soup_of(html), url, limit=self.MAX_LISTING_CRAWL)

    def _fetch(self, url):
        if url in self._html_cache:
            return self._html_cache[url]
        response = requests.get(url, headers=self._headers(), timeout=self.TIMEOUT)
        response.raise_for_status()
        self._html_cache[url] = response.text
        return response.text

    def _fetch_rendered(self, url):
        if self._browser is None:
            self._browser = BrowserFetcher()
        html = self._browser.fetch_rendered(url, self.USER_AGENT)
        self._html_cache[url] = html
        return html

    def _headers(self):
        return {
            "User-Agent": self.USER_AGENT,
            "Accept-Language": "es-EC,es;q=0.9,en;q=0.8",
        }

    def _shopify_products(self, url):
        parsed = urlparse(url)
        endpoint = f"{parsed.scheme}://{parsed.netloc}/products.json?limit=250"
        try:
            response = requests.get(endpoint, headers=self._headers(), timeout=self.TIMEOUT)
            if response.status_code != 200:
                return []
            payload = response.json()
        except (requests.RequestException, ValueError):
            return []

        products = []
        for item in payload.get("products") or []:
            product = self._from_shopify(item, parsed)
            if product:
                products.append(product)
        return products

    def _from_shopify(self, item, parsed_url):
        variants = item.get("variants") or []
        first_variant = variants[0] if variants else {}
        images = [image.get("src") for image in item.get("images") or [] if image.get("src")]

        product = engine.finalize(
            {
                "id": str(item.get("id") or ""),
                "name": item.get("title"),
                "url": f"{parsed_url.scheme}://{parsed_url.netloc}/products/{item.get('handle')}",
                "price": parse_price(first_variant.get("price")),
                "price_old": parse_price(first_variant.get("compare_at_price")),
                "sizes": self._shopify_options(item, ("size", "talla")),
                "colors": self._shopify_options(item, ("color",)),
                "description": re.sub(r"<[^>]+>", " ", item.get("body_html") or ""),
                "image_urls": images,
                "category": item.get("product_type") or "",
                "availability": "available"
                if any(variant.get("available") for variant in variants)
                else "out_of_stock",
                "extracted_at": parsers.now_iso(),
            },
            f"{parsed_url.scheme}://{parsed_url.netloc}",
        )
        return product if product and product.get("price") is not None else None

    def _shopify_options(self, item, names):
        for option in item.get("options") or []:
            if str(option.get("name", "")).lower() in names:
                return [str(value) for value in option.get("values") or []]
        return []
