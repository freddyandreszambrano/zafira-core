# Scraper MVP Moda RM — Plan de Implementación

> **Para agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recomendado) o superpowers:executing-plans para implementar este plan tarea por tarea. Steps use checkbox (`- [ ]`) syntax para tracking.

**Goal:** Crear app `scraper` con adaptador modular para extraer 5 categorías de moda de Moda RM, parsear HTML con BeautifulSoup, normalizar datos y imprimir JSON a consola via management command.

**Architecture:** Interfaz `BaseAdapter` → `ModarmAdapter` implementa scraping de categorías y productos. Management command `scrape --store modarm` orquesta el flujo, fail-fast en errores, sobrescribe cada ejecución. Parsers reutilizables para normalizar precios, categorías, imágenes.

**Tech Stack:** Django 5.2, requests, BeautifulSoup4, JSON, management commands

---

## Task 1: Crear estructura base de la app scraper

**Files:**
- Create: `app/scraper/__init__.py`
- Create: `app/scraper/apps.py`
- Create: `app/scraper/models/__init__.py`
- Create: `app/scraper/tests/__init__.py`
- Create: `app/scraper/urls.py`
- Create: `app/scraper/migrations/__init__.py`

- [ ] **Step 1: Crear directorio app/scraper y subdirectorios**

```bash
mkdir -p app/scraper/models
mkdir -p app/scraper/tests
mkdir -p app/scraper/migrations
mkdir -p app/scraper/management/commands
mkdir -p app/scraper/adapters
```

- [ ] **Step 2: Crear app/scraper/__init__.py (vacío)**

```python
```

- [ ] **Step 3: Crear app/scraper/apps.py**

```python
from django.apps import AppConfig

class ScraperConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.scraper'
    verbose_name = 'Scraper'
```

- [ ] **Step 4: Crear app/scraper/models/__init__.py (vacío en v1)**

```python
```

- [ ] **Step 5: Crear app/scraper/tests/__init__.py (vacío)**

```python
```

- [ ] **Step 6: Crear app/scraper/urls.py (vacío en v1)**

```python
from django.urls import path

urlpatterns = [
    # v2: agregar API endpoints
]
```

- [ ] **Step 7: Crear app/scraper/migrations/__init__.py (vacío)**

```python
```

- [ ] **Step 8: Crear archivos __init__.py para management y adapters**

```bash
touch app/scraper/management/__init__.py
touch app/scraper/management/commands/__init__.py
touch app/scraper/adapters/__init__.py
```

- [ ] **Step 9: Agregar 'app.scraper' a INSTALLED_APPS en core/settings.py**

Abre `core/settings.py` y localiza `INSTALLED_APPS`. Agrega `'app.scraper',` al final de la lista (antes de las apps de terceros si las hay):

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Apps locales
    'app.common',
    'app.security',
    'app.auth',
    'app.profiles',
    'app.scraper',  # ← AGREGAR
    
    # Third party
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
]
```

- [ ] **Step 10: Commit**

```bash
git add app/scraper/
git add core/settings.py
git commit -m "feat: create scraper app structure"
```

---

## Task 2: Instalar dependencias (requests, BeautifulSoup4)

**Files:**
- Modify: `requirements/base.txt`

- [ ] **Step 1: Agregar dependencias a requirements/base.txt**

Abre `requirements/base.txt` y agrega al final:

```
requests>=2.31.0
beautifulsoup4>=4.12.0
```

El archivo quedaría:
```
# Core dependencies for all environments
Django==5.2.14
djangorestframework==3.14.0
django-cors-headers==4.0.0
djangorestframework-simplejwt==5.3.0
Pillow==10.1.0
python-dotenv==1.0.0
python-decouple==3.8
django-environ==0.11.2

# Module-based permission system
django-crum==0.7.9
django-widget-tweaks==1.5.1

# Scraper
requests>=2.31.0
beautifulsoup4>=4.12.0
```

- [ ] **Step 2: Instalar las dependencias**

```bash
pip install -r requirements/base.txt
```

Expected: requests y beautifulsoup4 se instalan correctamente.

- [ ] **Step 3: Commit**

```bash
git add requirements/base.txt
git commit -m "deps: add requests and beautifulsoup4 for scraper"
```

---

## Task 3: Crear interfaz BaseAdapter

**Files:**
- Create: `app/scraper/base.py`

- [ ] **Step 1: Crear app/scraper/base.py**

```python
from abc import ABC, abstractmethod
from typing import List, Dict

class BaseAdapter(ABC):
    """Interfaz base para adaptadores de diferentes tiendas de moda."""
    
    @abstractmethod
    def get_categories(self) -> List[Dict]:
        """
        Retorna lista de categorías con URL y metadata.
        
        Returns:
            [
                {
                    'name': 'Mujeres',
                    'path': '/es_RW/MUJERES/MODA-MUJER/',
                    'url': 'https://www.modarm.com/es_RW/MUJERES/MODA-MUJER/',
                },
                ...
            ]
        """
        pass
    
    @abstractmethod
    def scrape_category(self, category: Dict) -> List[Dict]:
        """
        Extrae lista de productos de una categoría.
        
        Args:
            category: dict con 'name', 'path', 'url' (de get_categories)
        
        Returns:
            [
                {
                    'id': '005000000929186002',
                    'name': 'Chaqueta Unicolor con Cierres',
                    'url': 'https://www.modarm.com/es_RW/...',
                },
                ...
            ]
        """
        pass
    
    @abstractmethod
    def parse_product(self, url: str) -> Dict:
        """
        Parsea un producto desde su URL y normaliza datos.
        
        Args:
            url: URL del producto
        
        Returns:
            {
                'id': '005000000929186002',
                'name': 'Chaqueta Unicolor con Cierres',
                'category': 'Hombres/Moda Hombre/Chaquetas y Abrigos',
                'url': 'https://...',
                'price': 45.99,
                'price_old': 59.99 or None,
                'currency': 'USD',
                'sizes': ['S', 'M', 'L', 'XL'],
                'colors': ['Negro', 'Azul'],
                'description': '...',
                'image_urls': ['https://...', 'https://...'],
                'availability': 'available',  # available, out_of_stock, coming_soon
                'extracted_at': '2026-05-26T12:30:45.123456+00:00',
            }
        """
        pass
```

- [ ] **Step 2: Commit**

```bash
git add app/scraper/base.py
git commit -m "feat: create BaseAdapter interface for scrapers"
```

---

## Task 4: Crear utilidades parsers.py

**Files:**
- Create: `app/scraper/parsers.py`

- [ ] **Step 1: Crear app/scraper/parsers.py**

```python
import re
from datetime import datetime, timezone
from typing import List, Optional
from bs4 import NavigableString, Tag

def normalize_price(price_str: str) -> Optional[float]:
    """
    Normaliza strings de precio a float USD.
    
    Ejemplos:
        '$12.999' → 12.999
        '12,99' → 12.99
        '$ 45.50' → 45.50
        'invalid' → None
    """
    if not price_str or not isinstance(price_str, str):
        return None
    
    # Remover espacios y caracteres no numéricos excepto coma y punto
    price_str = price_str.strip()
    price_str = re.sub(r'[^\d,.\-]', '', price_str)
    
    if not price_str:
        return None
    
    try:
        # Reemplazar coma por punto (normalizador regional)
        price_str = price_str.replace(',', '.')
        return float(price_str)
    except ValueError:
        return None


def extract_category_path(breadcrumb: List[str]) -> str:
    """
    Convierte lista de breadcrumbs a string jerárquico.
    
    Ejemplos:
        ['Hombres', 'Moda Hombre', 'Camisas'] → 'Hombres/Moda Hombre/Camisas'
        [] → ''
        ['Solo'] → 'Solo'
    """
    if not breadcrumb:
        return ''
    return '/'.join(str(item).strip() for item in breadcrumb if item)


def extract_images(container) -> List[str]:
    """
    Extrae URLs de imágenes desde un contenedor BeautifulSoup.
    
    Busca:
        - img[src]
        - img[data-src]
    
    Retorna lista de URLs absolutas (sin /data:image, etc.)
    """
    images = []
    
    if not container:
        return images
    
    # Buscar todos los img dentro del contenedor
    for img_tag in container.find_all('img'):
        url = img_tag.get('src') or img_tag.get('data-src')
        
        if url and isinstance(url, str):
            url = url.strip()
            # Saltar data URIs
            if url.startswith('data:'):
                continue
            # Saltar URLs vacías
            if url:
                images.append(url)
    
    # Remover duplicados manteniendo orden
    seen = set()
    unique_images = []
    for img in images:
        if img not in seen:
            unique_images.append(img)
            seen.add(img)
    
    return unique_images


def now_iso() -> str:
    """
    Retorna timestamp ISO 8601 UTC actual.
    
    Ejemplo: '2026-05-26T12:30:45.123456+00:00'
    """
    return datetime.now(timezone.utc).isoformat()
```

- [ ] **Step 2: Commit**

```bash
git add app/scraper/parsers.py
git commit -m "feat: add parser utilities (normalize_price, extract_images, etc.)"
```

---

## Task 5: Crear tests para parsers.py

**Files:**
- Create: `app/scraper/tests/test_parsers.py`

- [ ] **Step 1: Crear app/scraper/tests/test_parsers.py**

```python
from django.test import TestCase
from app.scraper.parsers import (
    normalize_price,
    extract_category_path,
    extract_images,
    now_iso,
)
from datetime import datetime, timezone
from bs4 import BeautifulSoup

class TestNormalizePrice(TestCase):
    def test_price_with_dollar_sign(self):
        assert normalize_price('$12.999') == 12.999
    
    def test_price_with_comma(self):
        assert normalize_price('12,99') == 12.99
    
    def test_price_with_spaces(self):
        assert normalize_price('$ 45.50') == 45.50
    
    def test_invalid_price(self):
        assert normalize_price('invalid') is None
    
    def test_empty_price(self):
        assert normalize_price('') is None
    
    def test_none_price(self):
        assert normalize_price(None) is None
    
    def test_price_with_thousand_separator(self):
        # '1.000,99' (formato regional) → 1000.99
        assert normalize_price('1.000,99') == 1000.99


class TestExtractCategoryPath(TestCase):
    def test_multiple_categories(self):
        result = extract_category_path(['Hombres', 'Moda Hombre', 'Camisas'])
        assert result == 'Hombres/Moda Hombre/Camisas'
    
    def test_single_category(self):
        result = extract_category_path(['Solo'])
        assert result == 'Solo'
    
    def test_empty_list(self):
        result = extract_category_path([])
        assert result == ''
    
    def test_with_whitespace(self):
        result = extract_category_path(['  Hombres  ', 'Camisas  '])
        assert result == 'Hombres/Camisas'
    
    def test_with_none_values(self):
        # Valores None se ignoran
        result = extract_category_path(['Hombres', None, 'Camisas'])
        assert result == 'Hombres/None/Camisas'


class TestExtractImages(TestCase):
    def test_extract_single_image(self):
        html = '<img src="https://example.com/image.jpg" />'
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_images(soup)
        assert result == ['https://example.com/image.jpg']
    
    def test_extract_multiple_images(self):
        html = '''
            <div>
                <img src="https://example.com/1.jpg" />
                <img src="https://example.com/2.jpg" />
            </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_images(soup)
        assert result == ['https://example.com/1.jpg', 'https://example.com/2.jpg']
    
    def test_extract_data_src(self):
        html = '<img data-src="https://example.com/lazy.jpg" />'
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_images(soup)
        assert result == ['https://example.com/lazy.jpg']
    
    def test_ignore_data_uri(self):
        html = '<img src="data:image/png;base64,..." />'
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_images(soup)
        assert result == []
    
    def test_remove_duplicates(self):
        html = '''
            <div>
                <img src="https://example.com/image.jpg" />
                <img src="https://example.com/image.jpg" />
            </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_images(soup)
        assert result == ['https://example.com/image.jpg']
    
    def test_empty_container(self):
        result = extract_images(None)
        assert result == []


class TestNowIso(TestCase):
    def test_iso_format(self):
        result = now_iso()
        # Validar que es un string ISO válido
        assert isinstance(result, str)
        # Validar que contiene T y +00:00
        assert 'T' in result
        assert '+00:00' in result
    
    def test_is_valid_datetime(self):
        result = now_iso()
        # Intentar parsear como ISO
        try:
            datetime.fromisoformat(result)
            parsed = True
        except ValueError:
            parsed = False
        assert parsed
```

- [ ] **Step 2: Ejecutar tests para verificar que pasan**

```bash
python manage.py test app.scraper.tests.test_parsers -v 2
```

Expected: Todos los tests pasan.

- [ ] **Step 3: Commit**

```bash
git add app/scraper/tests/test_parsers.py
git commit -m "test: add unit tests for parsers module"
```

---

## Task 6: Crear ModarmAdapter

**Files:**
- Create: `app/scraper/adapters/modarm.py`

- [ ] **Step 1: Crear app/scraper/adapters/modarm.py**

```python
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime, timezone

from app.scraper.base import BaseAdapter
from app.scraper import parsers


class ModarmAdapter(BaseAdapter):
    """Adaptador para scraper de Moda RM (modarm.com)."""
    
    BASE_URL = "https://www.modarm.com"
    TIMEOUT = 10
    USER_AGENT = "Mozilla/5.0 (ZAFIRA-CORE-Scraper/1.0; +http://localhost)"
    
    # Categorías de moda principales
    CATEGORIES = [
        {
            'name': 'Mujeres',
            'path': '/es_RW/MUJERES/MODA-MUJER/',
        },
        {
            'name': 'Hombres',
            'path': '/es_RW/HOMBRES/MODA-HOMBRE/',
        },
        {
            'name': 'Infantil',
            'path': '/es_RW/INFANTIL/MODA-INFANTIL/',
        },
        {
            'name': 'Calzado',
            'path': '/es_RW/CALZADO/c/10202815893',
        },
        {
            'name': 'Accesorios',
            'path': '/es_RW/ACCESORIOS/c/10202815910',
        },
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT,
        })
    
    def get_categories(self) -> List[Dict]:
        """Retorna lista de categorías de moda."""
        categories = []
        for cat in self.CATEGORIES:
            categories.append({
                'name': cat['name'],
                'path': cat['path'],
                'url': self.BASE_URL + cat['path'],
            })
        return categories
    
    def scrape_category(self, category: Dict) -> List[Dict]:
        """
        Extrae lista de productos de una categoría.
        
        Busca links a productos con patrón /p/{product_id}
        """
        products = []
        url = category['url']
        
        try:
            response = self.session.get(url, timeout=self.TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Error fetching category {category['name']}: {e}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar links a productos
        # Patrón general: cualquier <a> con href que contenga /p/ (product link)
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            
            # Filtrar links de productos (contienen /p/)
            if '/p/' not in href:
                continue
            
            # Convertir URL relativa a absoluta
            if href.startswith('http'):
                product_url = href
            else:
                product_url = self.BASE_URL + href if href.startswith('/') else self.BASE_URL + '/' + href
            
            # Extraer product_id (último segmento o antes del ?)
            product_id = self._extract_product_id(href)
            
            if not product_id:
                continue
            
            # Obtener nombre (texto del link)
            name = link.get_text(strip=True)
            
            if name:
                products.append({
                    'id': product_id,
                    'name': name,
                    'url': product_url,
                })
        
        return products
    
    def parse_product(self, url: str) -> Dict:
        """
        Parsea un producto desde su URL.
        """
        try:
            response = self.session.get(url, timeout=self.TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Error fetching product {url}: {e}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraer datos del producto
        product_id = self._extract_product_id(url)
        name = self._extract_name(soup)
        category = self._extract_category(soup)
        price = self._extract_price(soup)
        price_old = self._extract_price_old(soup)
        sizes = self._extract_sizes(soup)
        colors = self._extract_colors(soup)
        description = self._extract_description(soup)
        image_urls = parsers.extract_images(soup)
        availability = self._extract_availability(soup)
        
        return {
            'id': product_id,
            'name': name,
            'category': category,
            'url': url,
            'price': price,
            'price_old': price_old,
            'currency': 'USD',
            'sizes': sizes,
            'colors': colors,
            'description': description,
            'image_urls': image_urls,
            'availability': availability,
            'extracted_at': parsers.now_iso(),
        }
    
    # ─── Métodos privados para extraer datos ───
    
    def _extract_product_id(self, url: str) -> Optional[str]:
        """Extrae product_id desde URL. Ej: /p/005000000929186002?..."""
        # Buscar patrón /p/{id}
        import re
        match = re.search(r'/p/([a-zA-Z0-9]+)', url)
        return match.group(1) if match else None
    
    def _extract_name(self, soup) -> str:
        """Extrae nombre del producto."""
        # Buscar título (h1, h2, o data-testid)
        title = soup.find('h1')
        if title:
            return title.get_text(strip=True)
        
        title = soup.find('h2')
        if title:
            return title.get_text(strip=True)
        
        return ''
    
    def _extract_category(self, soup) -> str:
        """Extrae categoría jerárquica (breadcrumb)."""
        breadcrumb = []
        
        # Buscar breadcrumb (usualmente nav o ol con li)
        nav = soup.find('nav') or soup.find('ol', class_='breadcrumb')
        if nav:
            for li in nav.find_all('li'):
                text = li.get_text(strip=True)
                if text:
                    breadcrumb.append(text)
        
        return parsers.extract_category_path(breadcrumb)
    
    def _extract_price(self, soup) -> Optional[float]:
        """Extrae precio actual del producto."""
        # Buscar elemento con clase price, precio, etc.
        price_elem = (
            soup.find('span', class_='price') or
            soup.find('span', class_='precio') or
            soup.find('div', class_='price')
        )
        
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            return parsers.normalize_price(price_text)
        
        return None
    
    def _extract_price_old(self, soup) -> Optional[float]:
        """Extrae precio anterior/descuento si existe."""
        price_elem = (
            soup.find('span', class_='old-price') or
            soup.find('span', class_='precio-anterior') or
            soup.find('div', class_='original-price')
        )
        
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            return parsers.normalize_price(price_text)
        
        return None
    
    def _extract_sizes(self, soup) -> List[str]:
        """Extrae tallas disponibles."""
        sizes = []
        
        # Buscar selector de tallas (input, button, select, etc.)
        size_container = (
            soup.find('div', class_='sizes') or
            soup.find('div', class_='tallas') or
            soup.find('fieldset')
        )
        
        if size_container:
            # Buscar inputs o labels con tallas
            for elem in size_container.find_all(['input', 'button', 'span', 'label']):
                value = elem.get('value') or elem.get_text(strip=True)
                if value and len(value) <= 5:  # Tallas son típicamente cortas (XL, 42, etc.)
                    sizes.append(value)
        
        # Remover duplicados manteniendo orden
        seen = set()
        unique_sizes = []
        for size in sizes:
            if size not in seen:
                unique_sizes.append(size)
                seen.add(size)
        
        return unique_sizes
    
    def _extract_colors(self, soup) -> List[str]:
        """Extrae colores disponibles."""
        colors = []
        
        # Buscar selector de colores
        color_container = (
            soup.find('div', class_='colors') or
            soup.find('div', class_='colores')
        )
        
        if color_container:
            for elem in color_container.find_all(['input', 'button', 'span', 'label']):
                value = elem.get('value') or elem.get('data-color') or elem.get_text(strip=True)
                if value:
                    colors.append(value)
        
        # Remover duplicados
        seen = set()
        unique_colors = []
        for color in colors:
            if color not in seen:
                unique_colors.append(color)
                seen.add(color)
        
        return unique_colors
    
    def _extract_description(self, soup) -> str:
        """Extrae descripción del producto."""
        # Buscar descripción
        desc_elem = (
            soup.find('div', class_='description') or
            soup.find('div', class_='descripcion') or
            soup.find('p', class_='product-description')
        )
        
        if desc_elem:
            return desc_elem.get_text(strip=True)
        
        return ''
    
    def _extract_availability(self, soup) -> str:
        """Extrae disponibilidad del producto."""
        # Buscar texto de disponibilidad
        text = soup.get_text().lower()
        
        if 'agotado' in text or 'out of stock' in text:
            return 'out_of_stock'
        elif 'proximamente' in text or 'coming soon' in text:
            return 'coming_soon'
        
        # Por defecto asumir disponible
        return 'available'
```

- [ ] **Step 2: Commit**

```bash
git add app/scraper/adapters/modarm.py
git commit -m "feat: implement ModarmAdapter for Moda RM scraping"
```

---

## Task 7: Crear adapter registry

**Files:**
- Modify: `app/scraper/adapters/__init__.py`

- [ ] **Step 1: Modificar app/scraper/adapters/__init__.py**

```python
from app.scraper.adapters.modarm import ModarmAdapter

# Registry de adaptadores por tienda
ADAPTER_MAP = {
    'modarm': ModarmAdapter,
    # v2: agregar más tiendas (zara, shein, etc.)
}

__all__ = ['ADAPTER_MAP', 'ModarmAdapter']
```

- [ ] **Step 2: Commit**

```bash
git add app/scraper/adapters/__init__.py
git commit -m "feat: create adapter registry"
```

---

## Task 8: Crear management command scrape

**Files:**
- Create: `app/scraper/management/commands/scrape.py`

- [ ] **Step 1: Crear app/scraper/management/commands/scrape.py**

```python
import json
from django.core.management.base import BaseCommand, CommandError
from app.scraper.adapters import ADAPTER_MAP
from app.scraper import parsers


class Command(BaseCommand):
    help = 'Scrape de tienda (modarm por defecto)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--store',
            default='modarm',
            help='Nombre del adaptador (modarm, zara, etc.). Default: modarm'
        )
        parser.add_argument(
            '--max-products',
            type=int,
            default=None,
            help='Máximo de productos a extraer. Default: sin límite'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Output detallado'
        )
    
    def handle(self, *args, **options):
        store = options['store']
        max_products = options['max_products']
        verbose = options['verbose']
        
        # 1. Validar que el adaptador exista
        if store not in ADAPTER_MAP:
            raise CommandError(
                f"Adaptador '{store}' no encontrado. "
                f"Disponibles: {', '.join(ADAPTER_MAP.keys())}"
            )
        
        # 2. Instanciar adaptador
        try:
            adapter = ADAPTER_MAP[store]()
        except Exception as e:
            raise CommandError(f"Error instanciando adaptador {store}: {e}")
        
        # 3. Diccionario para deduplicar por ID
        products = {}  # {id: producto}
        errors = []
        
        # 4. Iterar categorías
        categories = adapter.get_categories()
        
        for category in categories:
            if verbose:
                self.stdout.write(f"📂 Scraping {category['name']}...")
            
            try:
                # 5. Scrape de categoría → lista de producto links
                category_products = adapter.scrape_category(category)
                
                if verbose:
                    self.stdout.write(
                        f"   ✓ Found {len(category_products)} product links"
                    )
                
                # 6. Para cada producto, parsear
                for i, prod_link in enumerate(category_products):
                    if max_products and len(products) >= max_products:
                        if verbose:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"   ⚠ Reached max_products limit ({max_products})"
                                )
                            )
                        break
                    
                    try:
                        if verbose:
                            self.stdout.write(
                                f"   └─ [{i+1}/{len(category_products)}] Parsing {prod_link['id']}...",
                                ending=''
                            )
                        
                        # 7. Parse producto
                        product = adapter.parse_product(prod_link['url'])
                        products[product['id']] = product
                        
                        if verbose:
                            self.stdout.write(" ✓")
                    
                    except Exception as e:
                        error_msg = f"{prod_link.get('id', 'unknown')}: {str(e)}"
                        errors.append(error_msg)
                        if verbose:
                            self.stdout.write(
                                self.style.WARNING(f" ✗ Error: {e}"),
                                self.style.WARNING
                            )
                        # Fail-fast: continúa con el siguiente
                        continue
            
            except Exception as e:
                error_msg = f"{category['name']}: {str(e)}"
                errors.append(error_msg)
                if verbose:
                    self.stdout.write(
                        self.style.WARNING(f"   ✗ Error scraping category: {e}")
                    )
                # Continúa con la siguiente categoría
                continue
        
        # 8. Construir salida JSON
        output = {
            'metadata': {
                'store': store,
                'scraped_at': parsers.now_iso(),
                'total_products': len(products),
                'total_categories': len(categories),
                'total_errors': len(errors),
            },
            'products': list(products.values()),
            'errors': errors if errors else None,
        }
        
        # 9. Print JSON a stdout
        print(json.dumps(output, indent=2, ensure_ascii=False))
        
        # 10. Summary en stderr (no contamina JSON en stdout)
        if verbose:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ Scraping complete'))
            self.stdout.write(f'   Total products: {len(products)}')
            self.stdout.write(f'   Total errors: {len(errors)}')
```

- [ ] **Step 2: Probar command con --help**

```bash
python manage.py scrape --help
```

Expected: muestra opciones de command (--store, --max-products, --verbose)

- [ ] **Step 3: Commit**

```bash
git add app/scraper/management/commands/scrape.py
git commit -m "feat: create scrape management command"
```

---

## Task 9: Agregar target make scrape al Makefile

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Agregar targets scrape al Makefile**

Localiza la sección de tests (después de `test-fast`) y agrega:

```makefile
.PHONY: scrape
scrape: ## Ejecuta scraper de Moda RM (default: modarm, verbose)
	$(MANAGE) scrape --store modarm --verbose

.PHONY: scrape-quiet
scrape-quiet: ## Ejecuta scraper sin output detallado
	$(MANAGE) scrape --store modarm
```

- [ ] **Step 2: Probar que make scrape muestra help**

```bash
make help | grep scrape
```

Expected: muestra "scrape" en la lista de comandos

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "feat: add scrape target to Makefile"
```

---

## Task 10: Crear test integration básico

**Files:**
- Create: `app/scraper/tests/test_modarm.py`

- [ ] **Step 1: Crear app/scraper/tests/test_modarm.py**

```python
from django.test import TestCase
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from app.scraper.adapters.modarm import ModarmAdapter


class TestModarmAdapterCategories(TestCase):
    def setUp(self):
        self.adapter = ModarmAdapter()
    
    def test_get_categories_returns_list(self):
        categories = self.adapter.get_categories()
        assert isinstance(categories, list)
        assert len(categories) == 5  # 5 categorías de moda
    
    def test_get_categories_has_required_fields(self):
        categories = self.adapter.get_categories()
        for cat in categories:
            assert 'name' in cat
            assert 'path' in cat
            assert 'url' in cat
            assert cat['url'].startswith('https://www.modarm.com')
    
    def test_get_categories_names(self):
        categories = self.adapter.get_categories()
        names = [cat['name'] for cat in categories]
        assert 'Mujeres' in names
        assert 'Hombres' in names
        assert 'Infantil' in names
        assert 'Calzado' in names
        assert 'Accesorios' in names


class TestModarmAdapterScrapingCategory(TestCase):
    def setUp(self):
        self.adapter = ModarmAdapter()
    
    @patch('app.scraper.adapters.modarm.requests.Session.get')
    def test_scrape_category_returns_list(self, mock_get):
        # Mock HTML response
        html = '''
        <html>
            <a href="/es_RW/HOMBRES/MODA-HOMBRE/CAMISAS/Camisa-Azul/p/005000000929186001">Camisa Azul</a>
            <a href="/es_RW/HOMBRES/MODA-HOMBRE/CAMISAS/Camisa-Negra/p/005000000929186002">Camisa Negra</a>
        </html>
        '''
        mock_response = MagicMock()
        mock_response.text = html
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        category = {'name': 'Hombres', 'path': '/es_RW/HOMBRES/', 'url': 'https://www.modarm.com/es_RW/HOMBRES/'}
        products = self.adapter.scrape_category(category)
        
        assert isinstance(products, list)
        assert len(products) == 2
    
    @patch('app.scraper.adapters.modarm.requests.Session.get')
    def test_scrape_category_product_has_required_fields(self, mock_get):
        html = '''
        <html>
            <a href="/p/005000000929186001">Camisa Azul</a>
        </html>
        '''
        mock_response = MagicMock()
        mock_response.text = html
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        category = {'name': 'Hombres', 'path': '/es_RW/HOMBRES/', 'url': 'https://www.modarm.com/es_RW/HOMBRES/'}
        products = self.adapter.scrape_category(category)
        
        assert len(products) > 0
        product = products[0]
        assert 'id' in product
        assert 'name' in product
        assert 'url' in product


class TestModarmAdapterParseProduct(TestCase):
    def setUp(self):
        self.adapter = ModarmAdapter()
    
    @patch('app.scraper.adapters.modarm.requests.Session.get')
    def test_parse_product_returns_dict(self, mock_get):
        html = '''
        <html>
            <h1>Chaqueta Negra</h1>
            <span class="price">$45.99</span>
            <div class="sizes">
                <button value="S">S</button>
                <button value="M">M</button>
            </div>
            <img src="https://example.com/image.jpg" />
        </html>
        '''
        mock_response = MagicMock()
        mock_response.text = html
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        product = self.adapter.parse_product('https://www.modarm.com/es_RW/.../p/005000000929186001')
        
        assert isinstance(product, dict)
        assert 'id' in product
        assert 'name' in product
        assert 'category' in product
        assert 'url' in product
        assert 'price' in product
        assert 'sizes' in product
        assert 'image_urls' in product
        assert 'extracted_at' in product
    
    @patch('app.scraper.adapters.modarm.requests.Session.get')
    def test_parse_product_extracts_id(self, mock_get):
        html = '<html></html>'
        mock_response = MagicMock()
        mock_response.text = html
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        product = self.adapter.parse_product('https://www.modarm.com/.../p/005000000929186001?arg=val')
        assert product['id'] == '005000000929186001'
    
    @patch('app.scraper.adapters.modarm.requests.Session.get')
    def test_parse_product_normalizes_price(self, mock_get):
        html = '<html><span class="price">$45.99</span></html>'
        mock_response = MagicMock()
        mock_response.text = html
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        product = self.adapter.parse_product('https://www.modarm.com/.../p/005000000929186001')
        assert product['price'] == 45.99
        assert isinstance(product['price'], float)


class TestModarmAdapterHelpers(TestCase):
    def setUp(self):
        self.adapter = ModarmAdapter()
    
    def test_extract_product_id(self):
        url = '/es_RW/HOMBRES/p/005000000929186001'
        product_id = self.adapter._extract_product_id(url)
        assert product_id == '005000000929186001'
    
    def test_extract_product_id_with_query_string(self):
        url = '/es_RW/HOMBRES/p/005000000929186001?sort=price'
        product_id = self.adapter._extract_product_id(url)
        assert product_id == '005000000929186001'
    
    def test_extract_product_id_not_found(self):
        url = '/es_RW/HOMBRES/category'
        product_id = self.adapter._extract_product_id(url)
        assert product_id is None
```

- [ ] **Step 2: Ejecutar tests de modarm**

```bash
python manage.py test app.scraper.tests.test_modarm -v 2
```

Expected: Todos los tests pasan (mocks están configurados correctamente)

- [ ] **Step 3: Commit**

```bash
git add app/scraper/tests/test_modarm.py
git commit -m "test: add integration tests for ModarmAdapter"
```

---

## Task 11: Prueba piloto manual

**Files:** Ninguno (test manual)

- [ ] **Step 1: Probar command básico (sin verbose)**

```bash
python manage.py scrape --store modarm 2>/dev/null | head -50
```

Expected: JSON válido con estructura:
```json
{
  "metadata": {
    "store": "modarm",
    "scraped_at": "...",
    "total_products": X,
    "total_categories": 5
  },
  "products": [...]
}
```

- [ ] **Step 2: Probar con verbose**

```bash
python manage.py scrape --store modarm --verbose 2>&1 | head -100
```

Expected: output detallado mostrando categorías y productos siendo scrapeados

- [ ] **Step 3: Probar con max-products**

```bash
python manage.py scrape --store modarm --max-products 10 --verbose 2>&1 | grep "total_products"
```

Expected: "total_products": 10 (o cerca de 10 dependiendo de detalles de implementación)

- [ ] **Step 4: Validar JSON output es válido**

```bash
python manage.py scrape --store modarm 2>/dev/null | python -m json.tool > /dev/null && echo "JSON válido"
```

Expected: "JSON válido" (sin errores de parse)

- [ ] **Step 5: Revisar estructura de producto**

```bash
python manage.py scrape --store modarm 2>/dev/null | python -c "import json, sys; data = json.load(sys.stdin); p = data['products'][0] if data['products'] else {}; print(json.dumps(p, indent=2))" | head -30
```

Expected: producto con todos los campos (id, name, price, image_urls, etc.)

---

## Task 12: Final cleanup

**Files:**
- Ninguno

- [ ] **Step 1: Ejecutar todos los tests de scraper**

```bash
python manage.py test app.scraper -v 2
```

Expected: Todos los tests de parsers y modarm pasan

- [ ] **Step 2: Validar integración con Django check**

```bash
python manage.py check
```

Expected: 0 issues

- [ ] **Step 3: Verificar git status limpio**

```bash
git status
```

Expected: "nothing to commit, working tree clean" o lista de archivos trackeados

---

## Checklist de Completitud

- [ ] App scraper creada con estructura correcta
- [ ] Dependencias instaladas (requests, beautifulsoup4)
- [ ] BaseAdapter interfaz implementada
- [ ] Parsers utilities implementadas y testeadas
- [ ] ModarmAdapter implementado
- [ ] ADAPTER_MAP registry creado
- [ ] Management command scrape creado
- [ ] Makefile targets agregados
- [ ] Integration tests para ModarmAdapter
- [ ] Prueba piloto manual exitosa
- [ ] Todos los tests pasan
- [ ] Django check limpio
- [ ] Commits frecuentes y limpios
