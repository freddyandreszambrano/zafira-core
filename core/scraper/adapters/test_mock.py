from typing import Dict, List

from core.scraper.base import BaseAdapter


class TestMockAdapter(BaseAdapter):
    """Mock adapter for testing the scraper command."""

    SUPPORTED_DOMAINS = ("example.com",)

    def get_categories(self) -> List[Dict]:
        return [
            {"name": "Mock Category", "path": "/test/", "url": "https://example.com/test/"},
        ]

    def scrape_category(self, category: Dict) -> List[Dict]:
        return [
            {"id": "MOCK001", "name": "Test Product 1", "url": "https://example.com/p/MOCK001/"},
            {"id": "MOCK002", "name": "Test Product 2", "url": "https://example.com/p/MOCK002/"},
            {"id": "MOCK003", "name": "Test Product 3", "url": "https://example.com/p/MOCK003/"},
        ]

    def parse_product(self, url: str) -> Dict:
        product_id = url.split("/p/")[1].split("/")[0] if "/p/" in url else "UNKNOWN"

        return {
            "id": product_id,
            "name": f"Test Product {product_id}",
            "category": "Mock Category",
            "url": url,
            "price": 99.99,
            "price_old": 149.99,
            "currency": "USD",
            "sizes": ["XS", "S", "M", "L", "XL"],
            "colors": ["Black", "White", "Blue"],
            "description": "This is a test product for validating the scraper command.",
            "image_urls": [
                "https://example.com/image1.jpg",
                "https://example.com/image2.jpg",
                "https://example.com/image3.jpg",
            ],
            "availability": "available",
            "extracted_at": "2026-05-26T11:15:00+00:00",
        }
