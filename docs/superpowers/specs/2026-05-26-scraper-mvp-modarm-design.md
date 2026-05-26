# ZAFIRA-CORE Scraper MVP — Diseño Completo

**Fecha:** 2026-05-26  
**Objetivo:** Scraper para Moda RM, catálogo piloto (5 categorías de moda)  
**Salida:** JSON a consola, fail-fast, sobrescribe cada ejecución

---

## 1. Resumen

Crear app `scraper` con **adaptador modular** para extraer productos de [Moda RM](https://www.modarm.com/). La v1 extrae 5 categorías de moda (Mujeres, Hombres, Infantil, Calzado, Accesorios) usando **requests + BeautifulSoup**, parsea HTML, normaliza precios y datos, y imprime JSON a consola. 

**Restricciones v1:**
- Fail-fast: si un producto falla, se salta y continúa
- Sobrescribe: cada ejecución reemplaza la anterior (no histórico)
- Solo URLs de imágenes (sin descargar archivos)
- Selectores CSS hardcodeados en el adaptador (extensible en v2)

---

## 2. Arquitectura

### 2.1 Estructura de carpetas

```
app/scraper/
├── __init__.py
├── apps.py
├── management/
│   └── commands/
│       └── scrape.py                    # entry point: python manage.py scrape --store modarm
├── adapters/
│   ├── __init__.py                      # ADAPTER_MAP = {'modarm': ModarmAdapter, ...}
│   └── modarm.py                        # class ModarmAdapter(BaseAdapter)
├── base.py                              # class BaseAdapter (interfaz)
├── parsers.py                           # utilidades: normalize_price(), extract_images(), etc.
├── models/
│   └── __init__.py                      # (vacío en v1)
├── tests/
│   ├── __init__.py
│   └── test_modarm.py                   # unit + integration tests
├── urls.py                              # (vacío en v1)
└── migrations/
    └── __init__.py
```

### 2.2 Interfaz BaseAdapter

```python
# app/scraper/base.py

from abc import ABC, abstractmethod
from typing import List, Dict

class BaseAdapter(ABC):
    """Interfaz base para adaptadores de tiendas."""
    
    @abstractmethod
    def get_categories(self) -> List[Dict]:
        """
        Retorna lista de categorías.
        Formato: [
            {'name': 'Mujeres', 'path': '/es_RW/MUJERES/...', 'url': '...'},
            ...
        ]
        """
    
    @abstractmethod
    def scrape_category(self, category: Dict) -> List[Dict]:
        """
        Extrae productos de una categoría.
        Retorna lista de dicts con: {id, name, url, ...}
        """
    
    @abstractmethod
    def parse_product(self, url: str) -> Dict:
        """
        Parsea un producto desde su URL.
        Retorna dict normalizado: {
            id, name, category, url, price, price_old,
            sizes, colors, description, image_urls, availability, ...
        }
        """
```

### 2.3 ModarmAdapter

```python
# app/scraper/adapters/modarm.py

import requests
from bs4 import BeautifulSoup
from app.scraper.base import BaseAdapter
from app.scraper import parsers

class ModarmAdapter(BaseAdapter):
    BASE_URL = "https://www.modarm.com"
    TIMEOUT = 10
    USER_AGENT = "Mozilla/5.0 (ZAFIRA-CORE-Scraper/1.0)"
    
    CATEGORIES = [
        {
            'name': 'Mujeres',
            'path': '/es_RW/MUJERES/MODA-MUJER/',
            'subcategories': [
                {'name': 'Camisas', 'path': '...'},
                # ...
            ]
        },
        # Hombres, Infantil, Calzado, Accesorios
    ]
    
    def get_categories(self) -> List[Dict]:
        """Retorna categorías de moda."""
        return self.CATEGORIES
    
    def scrape_category(self, category: Dict) -> List[Dict]:
        """
        GET a category_url → BeautifulSoup
        Busca selector '.product-link' o similar
        Extrae id, name, url de cada producto
        Retorna [{'id': '005000000929186002', 'name': 'Chaqueta...', 'url': '...'}, ...]
        """
    
    def parse_product(self, url: str) -> Dict:
        """
        GET a product_url → BeautifulSoup
        Extrae: name, id (sku), precio, precios alternativos, tallas, colores, imágenes, descripción
        Normaliza precios con parsers.normalize_price()
        Extrae categoría jerárquica con parsers.extract_category_path()
        Extrae imágenes con parsers.extract_images()
        
        Retorna:
        {
            'id': '005000000929186002',
            'name': 'Chaqueta Unicolor con Cierres',
            'category': 'Hombres/Moda Hombre/Chaquetas y Abrigos',
            'url': 'https://www.modarm.com/es_RW/...',
            'price': 45.99,
            'price_old': 59.99,  # null si no hay descuento
            'currency': 'USD',
            'sizes': ['S', 'M', 'L', 'XL'],
            'colors': ['Negro', 'Azul'],
            'description': 'Chaqueta de alta calidad...',
            'image_urls': ['https://...', 'https://...'],
            'availability': 'available',  # available, out_of_stock, coming_soon
            'extracted_at': '2026-05-26T12:30:45Z'
        }
        """
```

### 2.4 Parsers (utilidades)

```python
# app/scraper/parsers.py

import re
from datetime import datetime, timezone
from typing import List, Optional

def normalize_price(price_str: str) -> Optional[float]:
    """
    Normaliza strings de precio a float USD.
    '$12.999' → 12.999
    '12,99' → 12.99
    None si no puede parsear
    """

def extract_category_path(breadcrumb: List[str]) -> str:
    """
    Convierte lista de breadcrumbs a string jerárquico.
    ['Hombres', 'Moda Hombre', 'Camisas'] → 'Hombres/Moda Hombre/Camisas'
    """

def extract_images(html_element) -> List[str]:
    """
    Busca img[src], img[data-src] en el HTML.
    Retorna lista de URLs absolutas.
    """

def now_iso() -> str:
    """Retorna timestamp ISO 8601 UTC."""
    return datetime.now(timezone.utc).isoformat()
```

### 2.5 Management Command

```python
# app/scraper/management/commands/scrape.py

from django.core.management.base import BaseCommand
import json
from app.scraper.adapters import ADAPTER_MAP

class Command(BaseCommand):
    help = "Scrape de tienda (modarm por defecto)"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--store',
            default='modarm',
            help="Nombre del adaptador (modarm, zara, etc.)"
        )
        parser.add_argument(
            '--max-products',
            type=int,
            default=None,
            help="Máximo de productos a extraer (None = sin límite)"
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help="Output detallado"
        )
    
    def handle(self, *args, **options):
        store = options['store']
        max_products = options['max_products']
        verbose = options['verbose']
        
        # 1. Cargar adaptador
        if store not in ADAPTER_MAP:
            self.stdout.write(self.style.ERROR(f"Adaptador '{store}' no encontrado"))
            return
        
        adapter = ADAPTER_MAP[store]()
        products = {}  # {id: producto}
        
        # 2. Iterar categorías
        for category in adapter.get_categories():
            if verbose:
                self.stdout.write(f"Scraping {category['name']}...")
            
            try:
                # 3. Scrape de categoría → lista de links
                category_products = adapter.scrape_category(category)
                
                for prod_link in category_products:
                    if max_products and len(products) >= max_products:
                        break
                    
                    try:
                        # 4. Parse producto
                        product = adapter.parse_product(prod_link['url'])
                        products[product['id']] = product
                    except Exception as e:
                        if verbose:
                            self.stdout.write(self.style.WARNING(f"Error parseando {prod_link['url']}: {e}"))
                        # Fail-fast: continúa con el siguiente
                        continue
            
            except Exception as e:
                if verbose:
                    self.stdout.write(self.style.WARNING(f"Error en categoría {category['name']}: {e}"))
                continue
        
        # 5. Construir salida
        output = {
            'metadata': {
                'store': store,
                'scraped_at': parsers.now_iso(),
                'total_products': len(products),
                'categories_count': len(adapter.get_categories())
            },
            'products': list(products.values())
        }
        
        # 6. Print JSON
        print(json.dumps(output, indent=2, ensure_ascii=False))
```

---

## 3. Flujo de ejecución

```
$ python manage.py scrape --store modarm --verbose

1. Cargar ModarmAdapter
2. Para cada categoría en CATEGORIES:
   - GET category_url
   - BeautifulSoup → extrae links /p/{id}
   - Para cada link:
     - GET product_url
     - BeautifulSoup → parsea producto
     - Normaliza datos
     - Agrega a dict {id: producto}
3. Deduplicar por ID (último gana)
4. Construir JSON con metadata
5. Print a stdout
```

---

## 4. Formato de salida (JSON)

```json
{
  "metadata": {
    "store": "modarm",
    "scraped_at": "2026-05-26T12:30:45.123456+00:00",
    "total_products": 145,
    "categories_count": 5
  },
  "products": [
    {
      "id": "005000000929186002",
      "name": "Chaqueta Unicolor con Cierres",
      "category": "Hombres/Moda Hombre/Chaquetas y Abrigos",
      "url": "https://www.modarm.com/es_RW/HOMBRES/MODA-HOMBRE/CHAQUETAS-Y-ABRIGOS/CHAQUETAS-Y-ABRIGOS/Chaqueta-Unicolor-con-Cierres/p/005000000929186002",
      "price": 45.99,
      "price_old": 59.99,
      "currency": "USD",
      "sizes": ["S", "M", "L", "XL"],
      "colors": ["Negro", "Azul"],
      "description": "Chaqueta de alta calidad con cierre frontal. Material transpirable...",
      "image_urls": [
        "https://modarm.com/images/005000000929186002-1.jpg",
        "https://modarm.com/images/005000000929186002-2.jpg"
      ],
      "availability": "available",
      "extracted_at": "2026-05-26T12:30:45.123456+00:00"
    },
    {
      "id": "005000000929186003",
      "name": "Chaqueta Negra Clásica",
      "category": "Hombres/Moda Hombre/Chaquetas y Abrigos",
      "url": "...",
      "price": 52.50,
      "price_old": null,
      "currency": "USD",
      "sizes": ["S", "M", "L"],
      "colors": ["Negro"],
      "description": "...",
      "image_urls": ["..."],
      "availability": "out_of_stock",
      "extracted_at": "2026-05-26T12:30:45.123456+00:00"
    }
  ]
}
```

---

## 5. Testing

### 5.1 Unit tests (parsers.py)
```python
# app/scraper/tests/test_modarm.py

class TestParsers(TestCase):
    def test_normalize_price(self):
        assert normalize_price('$12.999') == 12.999
        assert normalize_price('12,99') == 12.99
        assert normalize_price('invalid') is None
    
    def test_extract_category_path(self):
        assert extract_category_path(['A', 'B', 'C']) == 'A/B/C'
    
    def test_extract_images(self):
        html = '<img src="https://a.jpg" /><img src="https://b.jpg" />'
        # ...
```

### 5.2 Integration test
```python
class TestModarmAdapter(TestCase):
    def test_scrape_category_returns_products(self):
        # Mock requests.get
        # Llama adapter.scrape_category()
        # Valida que retorna list[dict] con id, name, url
    
    def test_parse_product_normalizes_data(self):
        # Mock requests.get con HTML real
        # Llama adapter.parse_product()
        # Valida todos los campos
```

### 5.3 Prueba piloto manual
```bash
make scrape  # alias para: python manage.py scrape --store modarm --verbose
# Valida:
# - Extrae ~100-150 productos
# - JSON formateado correctamente
# - Todos los campos presentes (id, name, price, image_urls, etc.)
# - Maneja productos con descuento y sin descuento
# - Maneja productos disponibles y agotados
# - Imágenes vienen como URLs (no descargadas)
```

---

## 6. Detalles de implementación

### 6.1 Selectores CSS para Moda RM
(Por investigar en scraping piloto)
- Categoría: buscar links en menú principal
- Producto en listado: selector para `.product-card`, `.product-link`, o similar
- Producto en detalle: titulo, precio, tallas, colores, imágenes, descripción

### 6.2 Manejo de errores
- **Categoría falla**: log warning, continúa con siguiente
- **Producto falla**: log warning (si `--verbose`), continúa
- **Timeout o error de red**: requests automáticamente reintenta (requests default)

### 6.3 Requisitos de dependencias
Agregar a `requirements/base.txt`:
```
requests>=2.31.0
beautifulsoup4>=4.12.0
```

---

## 7. Próximas fases (v2+)

- **Más tiendas**: agregar `adapters/zara.py`, `adapters/shein.py`, etc. (copy-paste + ajustes)
- **BD + API**: modelo `ScrapedProduct`, endpoint `/api/scraper/products/`
- **Descarga de imágenes**: opción `--download-images`, guardar a `data/modarm/images/`
- **Scheduler**: `celery` + crontab para scraping automático
- **Histórico**: guardar múltiples ejecuciones, comparar cambios de precio
- **Cache**: no re-scrapear productos sin cambios

---

## 8. Supuestos y restricciones

- **Responsable**: respetar `robots.txt` de Moda RM, no hacer DoS
- **Sin sesión**: v1 no intenta login, solo público
- **HTML estático**: requests + BeautifulSoup suficiente; Playwright solo si falla
- **Sin proxy**: asumir acceso directo a Moda RM desde dev/prod
- **Selectores**: si Moda RM cambia HTML, ajustar selectores en `modarm.py`
