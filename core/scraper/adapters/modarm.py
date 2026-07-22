import concurrent.futures
import sys
from typing import Dict, List, Optional
from urllib.parse import urljoin

from django.conf import settings

import requests
from bs4 import BeautifulSoup

from core.scraper import parsers
from core.scraper.base import BaseAdapter


class ModarmAdapter(BaseAdapter):
    """Adapter para Moda RM (modarm.com)."""

    BASE_URL = "https://www.modarm.com"
    SUPPORTED_DOMAINS = ("modarm.com",)
    TIMEOUT = 10
    USER_AGENT = "Mozilla/5.0 (ZAFIRA-CORE-Scraper/1.0; +http://localhost)"

    def __init__(self):
        self._playwright = None
        self._browser = None
        # Playwright (sync API) no puede correr dentro del hilo principal de
        # Django si este ya tiene un event loop activo. Se ejecuta siempre
        # en un hilo dedicado para evitar el error "cannot be called from
        # an async context".
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    @property
    def use_browser(self) -> bool:
        """Modo completo (con navegador) vs modo ligero (solo HTTP).

        En producción (Render free) se apaga con SCRAPER_USE_BROWSER=false:
        el Chromium headless no cabe en los 512MB de RAM y tumba el servicio.
        En local se deja encendido para el catálogo completo y el stock real.
        """
        return getattr(settings, "SCRAPER_USE_BROWSER", True)

    def _get_browser(self):
        """Lanza Chromium headless una sola vez y lo reutiliza para todas
        las verificaciones de stock durante este scrape."""
        if self._browser is None:
            from playwright.sync_api import sync_playwright

            if self._playwright is None:
                self._playwright = sync_playwright().start()
            try:
                self._browser = self._playwright.chromium.launch(headless=True)
            except Exception:
                # Si el launch falla hay que detener Playwright: dejarlo a medio
                # iniciar rompe todos los intentos siguientes en este hilo con
                # el error engañoso "Sync API inside the asyncio loop".
                self._playwright.stop()
                self._playwright = None
                raise
        return self._browser

    def _close_browser(self):
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def close(self):
        """Cierra el navegador headless. Debe llamarse al terminar el scrape."""
        try:
            self._executor.submit(self._close_browser).result()
        finally:
            self._executor.shutdown(wait=True)

    CATEGORIES = [
        {"name": "Mujer - Vestidos", "path": "/FALDAS-Y-VESTIDOS/c/10105230299"},
        {"name": "Mujer - Blusas", "path": "/BLUSAS/c/10105230099"},
        {"name": "Mujer - Pantalones", "path": "/JEANS-Y-PANTALONES/c/10105230399"},
        {"name": "Mujer - Chaquetas", "path": "/BLAZERS-Y-CONJUNTOS/c/10105229999"},
        {"name": "Hombre - Camisas", "path": "/CAMISAS/c/10202815899"},
        {"name": "Hombre - Camisetas", "path": "/CAMISETAS-Y-POLOS/c/10202815999"},
        {"name": "Hombre - Pantalones", "path": "/JEANS-Y-PANTALONES/c/10202816299"},
        {"name": "Hombre - Shorts", "path": "/SHORTS-Y-BERMUDAS/c/10202816399"},
        {"name": "Hombre - Chaquetas", "path": "/CHAQUETAS-Y-ABRIGOS/c/10202816099"},
    ]

    COLOR_KEYWORDS = [
        "Verde Oliva",
        "Azul Marino",
        "Azul Indigo",
        "Gris Jaspe",
        "Rosa Palo",
        "Vino Tinto",
        "Blanco Roto",
        "Negro",
        "Blanco",
        "Azul",
        "Rojo",
        "Verde",
        "Amarillo",
        "Rosado",
        "Rosa",
        "Gris",
        "Cafe",
        "Café",
        "Beige",
        "Camel",
        "Morado",
        "Lila",
        "Naranja",
        "Celeste",
        "Turquesa",
        "Dorado",
        "Plateado",
        "Vino",
        "Mostaza",
        "Oliva",
        "Crudo",
        "Marfil",
        "Coral",
        "Fucsia",
        "Khaki",
        "Caqui",
        "Lavanda",
    ]

    def get_categories(self) -> List[Dict]:
        """Retorna lista de categorías soportadas."""
        return [
            {
                "name": cat["name"],
                "path": cat["path"],
                "url": f"{self.BASE_URL}{cat['path']}",
            }
            for cat in self.CATEGORIES
        ]

    def scrape_category(self, category: Dict) -> List[Dict]:
        """
        Extrae lista de productos de una categoría.

        Args:
            category: dict con 'name', 'path', 'url'

        Returns:
            Lista de dicts con 'id', 'name', 'url'
        """
        products = []
        url = category["url"]

        # Los errores deben subir hasta services para llegar al array `errors`
        # de la respuesta; tragarlos aquí producía "éxito" con 0 productos.
        html = self._executor.submit(self._fetch_category_html, url).result()

        soup = BeautifulSoup(html, "html.parser")

        product_links = soup.find_all("a", href=True)
        seen = set()

        for link in product_links:
            href = link.get("href", "")
            if "/p/" not in href:
                continue

            product_id = self._extract_product_id(href)
            if product_id in seen:
                continue
            product_name = self._extract_name(link)

            if not product_id or not product_name:
                continue
            seen.add(product_id)

            product_url = urljoin(self.BASE_URL, href)

            products.append(
                {
                    "id": product_id,
                    "name": product_name,
                    "url": product_url,
                }
            )

        return products

    def _fetch_category_html(self, url: str) -> str:
        """
        Carga la página de categoría con un navegador real y hace scroll
        hasta que deje de aparecer contenido nuevo (scroll infinito), ya
        que el listado completo no está disponible en el HTML estático.

        En modo ligero (sin navegador) se cae al HTML estático, que igual
        trae las prendas de la primera página (~24) — suficiente para
        escaneos con límite.
        """
        if not self.use_browser:
            return self._fetch_category_html_static(url)

        browser = self._get_browser()
        page = browser.new_page(user_agent=self.USER_AGENT)
        page.route(
            "**/*",
            lambda route: route.abort()
            if route.request.resource_type in ("image", "font", "media")
            else route.continue_(),
        )
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            previous_count = -1
            stable_rounds = 0
            for _ in range(40):
                current_count = page.eval_on_selector_all(
                    "a[href*='/p/']", "elements => elements.length"
                )
                if current_count == previous_count:
                    stable_rounds += 1
                    if stable_rounds >= 2:
                        break
                else:
                    stable_rounds = 0
                previous_count = current_count
                page.mouse.wheel(0, 2500)
                page.wait_for_timeout(600)
            return page.content()
        finally:
            page.close()

    def _fetch_category_html_static(self, url: str) -> str:
        """Modo ligero: trae el HTML de la categoría con una petición normal,
        sin navegador. Solo llegan las prendas de la primera página (~24, sin
        el scroll infinito), pero es suficiente para escaneos con límite y no
        consume la memoria que tumba el servidor gratis."""
        headers = {"User-Agent": self.USER_AGENT}
        response = requests.get(url, headers=headers, timeout=self.TIMEOUT)
        response.raise_for_status()
        return response.text

    def parse_product(self, url: str) -> Dict:
        """
        Parsea un producto desde su URL y normaliza datos.

        Args:
            url: URL del producto

        Returns:
            Dict con campos normalizados del producto
        """
        result = {
            "id": None,
            "name": None,
            "category": None,
            "url": url,
            "price": None,
            "price_old": None,
            "currency": "USD",
            "sizes": [],
            "colors": [],
            "description": None,
            "image_urls": [],
            "availability": "unknown",
            "extracted_at": parsers.now_iso(),
        }

        headers = {"User-Agent": self.USER_AGENT}
        response = requests.get(url, headers=headers, timeout=self.TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        result["id"] = self._extract_product_id(url)
        result["name"] = self._extract_name(soup)
        result["category"] = self._extract_category(soup)
        result["price"] = self._extract_price(soup)
        result["price_old"] = self._extract_price_old(soup)
        size_options = self._extract_size_options(soup)
        result["sizes"] = self._check_sizes_availability(size_options)
        result["colors"] = self._extract_colors(soup)
        result["description"] = self._extract_description(soup)
        result["image_urls"] = self._extract_images(soup)
        result["availability"] = self._extract_availability(soup)

        return result

    def _extract_product_id(self, url_or_href: str) -> Optional[str]:
        """
        Extrae ID del producto desde URL o href.

        Busca patrón: /p/<id>/ o /p/<id>
        """
        if "/p/" not in url_or_href:
            return None

        try:
            parts = url_or_href.split("/p/")
            if len(parts) < 2:
                return None

            id_part = parts[1].split("/")[0].split("?")[0]
            return id_part if id_part else None
        except (IndexError, AttributeError):
            return None

    def _extract_name(self, element) -> Optional[str]:
        """
        Extrae nombre del producto.

        Busca en: <h1>, <h2> con clase 'product-name', <a> data-product-name, o text del link.
        """
        if element is None:
            return None

        if hasattr(element, "name") and element.name == "a":
            name = element.get("data-product-name", "").strip()
            if name:
                return name

            name = element.get("title", "").strip()
            if name:
                return name

            name = element.get_text(strip=True)
            if name:
                return name

        if hasattr(element, "find"):
            page_title_name = element.select_one(".product-details.page-title .name")
            if page_title_name:
                name = self._direct_text(page_title_name)
                if name:
                    return name

            name_elem = element.select_one("div.name")
            if name_elem:
                name = self._direct_text(name_elem)
                if name:
                    return name

            h1 = element.find("h1")
            if h1:
                name = h1.get_text(strip=True)
                if name and name.lower() != "antes de empezar a comprar":
                    return name

            h2 = element.find("h2")
            if h2:
                name = h2.get_text(strip=True)
                if name and name.lower() != "antes de empezar a comprar":
                    return name

            product_name = element.find(class_="product-name")
            if product_name:
                return product_name.get_text(strip=True)

        return None

    def _extract_category(self, soup) -> Optional[str]:
        """
        Extrae categoría del producto desde breadcrumb.

        Busca: <nav> con clase 'breadcrumb', <ol>, o estructura similar.
        """
        if soup is None:
            return None

        breadcrumb = soup.find("nav", class_="breadcrumb")
        if not breadcrumb:
            breadcrumb = soup.find("ol", class_="breadcrumb")

        if breadcrumb:
            items = breadcrumb.find_all("li")
            breadcrumb_list = [item.get_text(strip=True) for item in items]
            breadcrumb_list = [
                item for item in breadcrumb_list if item and item.lower() != "inicio"
            ]
            if breadcrumb_list:
                breadcrumb_list = breadcrumb_list[:-1]
            return parsers.extract_category_path(breadcrumb_list)

        return None

    def _extract_price(self, soup) -> Optional[float]:
        """
        Extrae precio actual del producto.

        Busca: <span> con clase 'price', 'current-price', o data-price.
        """
        if soup is None:
            return None

        selectors = [
            ".price-panel .priceDiscountDetails",
            ".price-panel .priceRegularDetails",
            ".price-panel .pdp-prices-box .direct-credit-price",
            ".priceDiscount",
            "span.price",
            "span.current-price",
            ".product-price",
        ]
        price_elem = self._select_first(soup, selectors)

        if price_elem:
            price_text = price_elem.get_text(strip=True)
            return parsers.normalize_price(price_text)

        return None

    def _extract_price_old(self, soup) -> Optional[float]:
        """
        Extrae precio anterior (descuento) si existe.

        Busca: <span> con clase 'old-price', 'original-price', etc.
        """
        if soup is None:
            return None

        selectors = [
            ".price-panel .priceOldDetails",
            ".priceOld",
            "span.old-price",
            "span.original-price",
            "s",
        ]
        price_elem = self._select_first(soup, selectors)

        if price_elem:
            price_text = price_elem.get_text(strip=True)
            return parsers.normalize_price(price_text)

        return None

    def _extract_size_options(self, soup) -> List[Dict]:
        """
        Extrae las tallas que la prenda maneja, junto con la URL propia
        de cada talla (necesaria para verificar su stock real).

        Busca: <select> con name='size', <div> con clase 'size-options',
        o el selector de variantes <select id="priority1">.
        """
        options = []

        if soup is None:
            return options

        size_select = soup.find("select", {"name": "size"})
        if size_select:
            for opt in size_select.find_all("option"):
                label = opt.get_text(strip=True)
                if label and label.lower() != "select":
                    options.append({"label": label, "url": None})
            return options

        size_options = soup.find("div", class_="size-options")
        if size_options:
            for btn in size_options.find_all(["button", "span"]):
                label = btn.get_text(strip=True)
                if label:
                    options.append({"label": label, "url": None})
            return options

        variant_select = soup.find("select", id="priority1")
        if variant_select:
            for opt in variant_select.find_all("option"):
                label = opt.get_text(strip=True)
                href = opt.get("value")
                if label:
                    options.append({"label": label, "url": href})
            return options

        return options

    def _check_sizes_availability(self, size_options: List[Dict]) -> List[str]:
        """
        Verifica con un navegador real (Chromium headless) qué tallas
        tienen stock real, ya que el sitio resuelve esto con JavaScript
        y no aparece en el HTML estático.

        Se ejecuta en el hilo dedicado de Playwright (ver __init__).

        En modo ligero (sin navegador) se devuelven todas las tallas que
        ofrece la prenda sin verificar stock: es el precio de no abrir
        Chromium en el servidor gratis.
        """
        if not size_options:
            return []

        if not self.use_browser:
            return [option["label"] for option in size_options]

        try:
            return self._executor.submit(self._check_sizes_availability_sync, size_options).result()
        except Exception as e:
            print(f"No se pudo verificar stock de tallas: {e}", file=sys.stderr)
            return [option["label"] for option in size_options]

    def _check_sizes_availability_sync(self, size_options: List[Dict]) -> List[str]:
        available = []

        browser = self._get_browser()
        page = browser.new_page(user_agent=self.USER_AGENT)
        # Bloquear imagenes/fuentes/multimedia: no se necesitan para leer el
        # estado del boton, y evitan que la pagina se quede "ocupada" cargando
        # recursos pesados que ralentizan cada verificacion.
        page.route(
            "**/*",
            lambda route: route.abort()
            if route.request.resource_type in ("image", "font", "media")
            else route.continue_(),
        )

        try:
            for option in size_options:
                label = option["label"]
                href = option.get("url")

                if not href:
                    available.append(label)
                    continue

                full_url = urljoin(self.BASE_URL, href)
                try:
                    page.goto(full_url, wait_until="domcontentloaded", timeout=15000)
                    try:
                        page.wait_for_selector("#addToCartButton", timeout=8000)
                    except Exception:
                        pass
                    page.wait_for_timeout(500)
                    button = page.query_selector("#addToCartButton")
                    is_disabled = button.get_attribute("disabled") is not None if button else True
                    if not is_disabled:
                        available.append(label)
                except Exception as e:
                    print(f"Error verificando stock de talla {label}: {e}", file=sys.stderr)
        finally:
            page.close()

        return available

    def _extract_colors(self, soup) -> List[str]:
        """
        Extrae colores disponibles.

        Busca el bloque <div class="variant-name">Color</div> seguido de
        <ul class="variant-list"> con cada color como <a class="swatchVariant">.
        El title de cada swatch es el nombre completo del producto de esa
        variante, así que se extrae la palabra de color conocida dentro de él.
        """
        colors = []

        if soup is None:
            return colors

        for name_div in soup.find_all("div", class_="variant-name"):
            if name_div.get_text(strip=True).lower() != "color":
                continue

            container = name_div.parent
            if not container:
                continue

            variant_list = container.find("ul", class_="variant-list")
            if not variant_list:
                continue

            for item in variant_list.find_all("a", class_="swatchVariant"):
                img = item.find("img")
                label = None
                if img:
                    label = img.get("title") or img.get("alt")
                if not label:
                    label = item.get_text(strip=True)
                if not label:
                    continue

                color_name = self._match_color_keyword(label)
                if color_name:
                    colors.append(color_name)

            break

        return colors

    def _match_color_keyword(self, label: str) -> Optional[str]:
        label_lower = label.lower()
        for keyword in self.COLOR_KEYWORDS:
            if keyword.lower() in label_lower:
                return keyword
        return None

    def _extract_images(self, soup) -> List[str]:
        images = []
        seen = set()

        selectors = (
            ".product-main-info img, .product-image-gallery img, .gallery-carousel img, img.lazyOwl"
        )
        for img in soup.select(selectors):
            url = img.get("data-zoom-image") or img.get("data-src") or img.get("src")
            if not self._is_product_image(url):
                continue
            full_url = urljoin(self.BASE_URL, url)
            if full_url not in seen:
                images.append(full_url)
                seen.add(full_url)

        if images:
            return images

        for url in parsers.extract_images(soup):
            if not self._is_product_image(url):
                continue
            full_url = urljoin(self.BASE_URL, url)
            if full_url not in seen:
                images.append(full_url)
                seen.add(full_url)
        return images

    def _extract_description(self, soup) -> Optional[str]:
        """
        Extrae descripción del producto.

        Busca: <div> con clase 'description', 'product-description', etc.
        """
        if soup is None:
            return None

        desc_elem = soup.find("div", class_="description")
        if not desc_elem:
            desc_elem = soup.find("div", class_="product-description")
        if not desc_elem:
            desc_elem = soup.find("section", class_="description")

        if desc_elem:
            return desc_elem.get_text(strip=True)

        return None

    def _extract_availability(self, soup) -> str:
        """
        Extrae estado de disponibilidad.

        Retorna: 'available', 'out_of_stock', o 'unknown'
        Busca textos como "Agotado", "Out of Stock", o elementos con clase availability.
        """
        if soup is None:
            return "unknown"

        avail_elem = soup.find(class_="availability")
        if avail_elem:
            text = avail_elem.get_text(strip=True).lower()
            if "agotado" in text or "out of stock" in text or "no disponible" in text:
                return "out_of_stock"
            if "disponible" in text or "available" in text:
                return "available"

        page_text = soup.get_text().lower()
        if "agotado" in page_text or "out of stock" in page_text:
            return "out_of_stock"

        return "available"

    def _select_first(self, soup, selectors):
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                return elem
        return None

    def _direct_text(self, element) -> Optional[str]:
        texts = [
            text.strip()
            for text in element.find_all(string=True, recursive=False)
            if text and text.strip()
        ]
        return texts[0] if texts else None

    def _is_product_image(self, url) -> bool:
        if not url or url.startswith("data:"):
            return False

        lowered = url.lower()
        path = lowered.split("?", 1)[0]
        if not path.endswith((".webp", ".jpg", ".jpeg", ".png")):
            return False

        blocked = ("logo", "lupa_", "wsplogo", "color-pago", "banner", "primera-compra")
        if any(item in lowered for item in blocked):
            return False

        size_markers = ("-1200-", "-515-", "-96-", "x1200-", "x900-")
        return "/medias/" in path and any(size in path for size in size_markers)
