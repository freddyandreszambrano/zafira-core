import sys
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from core.scraper import parsers
from core.scraper.base import BaseAdapter


class ModarmAdapter(BaseAdapter):
    """Adapter para Moda RM (modarm.com)."""

    BASE_URL = "https://www.modarm.com"
    TIMEOUT = 10
    USER_AGENT = "Mozilla/5.0 (ZAFIRA-CORE-Scraper/1.0; +http://localhost)"

    CATEGORIES = [
        {'name': 'Mujeres', 'path': '/es_RW/MUJERES/MODA-MUJER/'},
        {'name': 'Hombres', 'path': '/es_RW/HOMBRES/MODA-HOMBRE/'},
        {'name': 'Infantil', 'path': '/es_RW/INFANTIL/MODA-INFANTIL/'},
        {'name': 'Calzado', 'path': '/es_RW/CALZADO/CALZADO-GENERAL/'},
        {'name': 'Accesorios', 'path': '/es_RW/ACCESORIOS/ACCESORIOS-GENERAL/'},
    ]

    def get_categories(self) -> List[Dict]:
        """Retorna lista de categorías soportadas."""
        return [
            {
                'name': cat['name'],
                'path': cat['path'],
                'url': f"{self.BASE_URL}{cat['path']}",
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
        url = category['url']

        try:
            headers = {'User-Agent': self.USER_AGENT}
            response = requests.get(url, headers=headers, timeout=self.TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            product_links = soup.find_all('a', href=True)
            seen = set()

            for link in product_links:
                href = link.get('href', '')
                if '/p/' not in href:
                    continue

                product_id = self._extract_product_id(href)
                if product_id in seen:
                    continue
                product_name = self._extract_name(link)

                if not product_id or not product_name:
                    continue
                seen.add(product_id)

                product_url = urljoin(self.BASE_URL, href)

                products.append({
                    'id': product_id,
                    'name': product_name,
                    'url': product_url,
                })

        except requests.RequestException as e:
            print(f"Error scraping category {category['name']}: {e}", file=sys.stderr)

        return products

    def parse_product(self, url: str) -> Dict:
        """
        Parsea un producto desde su URL y normaliza datos.

        Args:
            url: URL del producto

        Returns:
            Dict con campos normalizados del producto
        """
        result = {
            'id': None,
            'name': None,
            'category': None,
            'url': url,
            'price': None,
            'price_old': None,
            'currency': 'USD',
            'sizes': [],
            'colors': [],
            'description': None,
            'image_urls': [],
            'availability': 'unknown',
            'extracted_at': parsers.now_iso(),
        }

        try:
            headers = {'User-Agent': self.USER_AGENT}
            response = requests.get(url, headers=headers, timeout=self.TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            result['id'] = self._extract_product_id(url)
            result['name'] = self._extract_name(soup)
            result['category'] = self._extract_category(soup)
            result['price'] = self._extract_price(soup)
            result['price_old'] = self._extract_price_old(soup)
            result['sizes'] = self._extract_sizes(soup)
            result['colors'] = self._extract_colors(soup)
            result['description'] = self._extract_description(soup)
            result['image_urls'] = self._extract_images(soup)
            result['availability'] = self._extract_availability(soup)

        except requests.RequestException as e:
            print(f"Error parsing product {url}: {e}", file=sys.stderr)

        return result

    def _extract_product_id(self, url_or_href: str) -> Optional[str]:
        """
        Extrae ID del producto desde URL o href.

        Busca patrón: /p/<id>/ o /p/<id>
        """
        if '/p/' not in url_or_href:
            return None

        try:
            parts = url_or_href.split('/p/')
            if len(parts) < 2:
                return None

            id_part = parts[1].split('/')[0].split('?')[0]
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

        if hasattr(element, 'name') and element.name == 'a':
            name = element.get('data-product-name', '').strip()
            if name:
                return name

            name = element.get('title', '').strip()
            if name:
                return name

            name = element.get_text(strip=True)
            if name:
                return name

        if hasattr(element, 'find'):
            page_title_name = element.select_one('.product-details.page-title .name')
            if page_title_name:
                name = self._direct_text(page_title_name)
                if name:
                    return name

            name_elem = element.select_one('div.name')
            if name_elem:
                name = self._direct_text(name_elem)
                if name:
                    return name

            h1 = element.find('h1')
            if h1:
                name = h1.get_text(strip=True)
                if name and name.lower() != 'antes de empezar a comprar':
                    return name

            h2 = element.find('h2')
            if h2:
                name = h2.get_text(strip=True)
                if name and name.lower() != 'antes de empezar a comprar':
                    return name

            product_name = element.find(class_='product-name')
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

        breadcrumb = soup.find('nav', class_='breadcrumb')
        if not breadcrumb:
            breadcrumb = soup.find('ol', class_='breadcrumb')

        if breadcrumb:
            items = breadcrumb.find_all('li')
            breadcrumb_list = [item.get_text(strip=True) for item in items]
            breadcrumb_list = [
                item for item in breadcrumb_list
                if item and item.lower() != 'inicio'
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
            '.price-panel .priceDiscountDetails',
            '.price-panel .priceRegularDetails',
            '.price-panel .pdp-prices-box .direct-credit-price',
            '.priceDiscount',
            'span.price',
            'span.current-price',
            '.product-price',
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
            '.price-panel .priceOldDetails',
            '.priceOld',
            'span.old-price',
            'span.original-price',
            's',
        ]
        price_elem = self._select_first(soup, selectors)

        if price_elem:
            price_text = price_elem.get_text(strip=True)
            return parsers.normalize_price(price_text)

        return None

    def _extract_sizes(self, soup) -> List[str]:
        """
        Extrae tallas disponibles.

        Busca: <select> con name='size', <div> con clase 'size-options', etc.
        """
        sizes = []

        if soup is None:
            return sizes

        size_select = soup.find('select', {'name': 'size'})
        if size_select:
            options = size_select.find_all('option')
            for opt in options:
                size = opt.get_text(strip=True)
                if size and size.lower() != 'select':
                    sizes.append(size)
            return sizes

        size_options = soup.find('div', class_='size-options')
        if size_options:
            buttons = size_options.find_all(['button', 'span'])
            for btn in buttons:
                size = btn.get_text(strip=True)
                if size:
                    sizes.append(size)
            return sizes

        variant_select = soup.find('select', id='priority1')
        if variant_select:
            for opt in variant_select.find_all('option'):
                size = opt.get_text(strip=True)
                if size:
                    sizes.append(size)
            return sizes

        return sizes

    def _extract_colors(self, soup) -> List[str]:
        """
        Extrae colores disponibles.

        Busca: <select> con name='color', <div> con clase 'color-options', etc.
        """
        colors = []

        if soup is None:
            return colors

        color_select = soup.find('select', {'name': 'color'})
        if color_select:
            options = color_select.find_all('option')
            for opt in options:
                color = opt.get_text(strip=True)
                if color and color.lower() != 'select':
                    colors.append(color)
            return colors

        color_options = soup.find('div', class_='color-options')
        if color_options:
            buttons = color_options.find_all(['button', 'span'])
            for btn in buttons:
                color = btn.get_text(strip=True)
                if color:
                    colors.append(color)
            return colors

        return colors

    def _extract_images(self, soup) -> List[str]:
        images = []
        seen = set()

        selectors = '.product-main-info img, .product-image-gallery img, .gallery-carousel img, img.lazyOwl'
        for img in soup.select(selectors):
            url = img.get('data-zoom-image') or img.get('data-src') or img.get('src')
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

        desc_elem = soup.find('div', class_='description')
        if not desc_elem:
            desc_elem = soup.find('div', class_='product-description')
        if not desc_elem:
            desc_elem = soup.find('section', class_='description')

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
            return 'unknown'

        avail_elem = soup.find(class_='availability')
        if avail_elem:
            text = avail_elem.get_text(strip=True).lower()
            if 'agotado' in text or 'out of stock' in text or 'no disponible' in text:
                return 'out_of_stock'
            if 'disponible' in text or 'available' in text:
                return 'available'

        page_text = soup.get_text().lower()
        if 'agotado' in page_text or 'out of stock' in page_text:
            return 'out_of_stock'

        return 'available'

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
        if not url or url.startswith('data:'):
            return False

        lowered = url.lower()
        path = lowered.split('?', 1)[0]
        if not path.endswith(('.webp', '.jpg', '.jpeg', '.png')):
            return False

        blocked = ('logo', 'lupa_', 'wsplogo', 'color-pago', 'banner', 'primera-compra')
        if any(item in lowered for item in blocked):
            return False

        return '/medias/' in path and any(size in path for size in ('-1200-', '-515-', '-96-'))
