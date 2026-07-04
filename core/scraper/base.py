from abc import ABC, abstractmethod
from typing import Dict, List
from urllib.parse import urlparse


class BaseAdapter(ABC):
    """Interfaz base para adaptadores de diferentes tiendas de moda."""

    SUPPORTED_DOMAINS = ()

    @classmethod
    def supports_url(cls, url):
        hostname = urlparse(url).hostname or ""
        hostname = hostname.lower()
        return any(
            hostname == domain or hostname.endswith(f".{domain}")
            for domain in cls.SUPPORTED_DOMAINS
        )

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
