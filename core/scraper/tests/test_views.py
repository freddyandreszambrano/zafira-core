import json

from django.test import TestCase
from django.urls import reverse

from core.auth.models import User
from core.scraper.models import Product, ScraperSource


class TestScraperScanView(TestCase):
    def setUp(self):
        self.url = reverse("scraper_scan")
        self.user = User.objects.create_superuser(
            username="scraper_admin",
            email="scraper@example.com",
            password="testpass123",
            dni="9999999999",
        )

    def test_get_requires_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_get_renders_scan_page_for_logged_user(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "scraper/scan.html")
        self.assertContains(response, "Scraper")

    def test_post_scan_returns_json(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                "action": "scan",
                "store": "test_mock",
                "url": "https://example.com/test/",
                "max_products": "2",
            },
        )
        payload = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["metadata"]["total_products"], 2)
        self.assertEqual(payload["products"][0]["id"], "MOCK001")

    def test_post_scan_previews_without_saving(self):
        self.client.force_login(self.user)

        self.client.post(
            self.url,
            {"action": "scan", "url": "https://example.com/test/", "max_products": "2"},
        )

        self.assertEqual(Product.objects.count(), 0)

    def test_post_save_products_persists_payload(self):
        self.client.force_login(self.user)

        products = [
            {
                "id": "MOCK001",
                "name": "Test Product MOCK001",
                "category": "Mujer/Vestidos",
                "url": "https://example.com/p/MOCK001/",
                "price": 99.99,
                "currency": "USD",
                "sizes": ["S", "M"],
                "colors": ["Negro"],
                "image_urls": ["https://example.com/image1.jpg"],
                "availability": "available",
                "extracted_at": "2026-07-05T10:00:00+00:00",
            }
        ]
        response = self.client.post(
            self.url,
            {
                "action": "save_products",
                "store": "test_mock",
                "products": json.dumps(products),
            },
        )
        payload = json.loads(response.content)

        self.assertTrue(payload["success"])
        self.assertEqual(payload["saved"], {"created": 1, "updated": 0, "skipped": 0})
        self.assertEqual(Product.objects.get(id_external="MOCK001").store, "test_mock")

    def test_post_save_products_without_payload_returns_error(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {"action": "save_products", "store": "test_mock", "products": "[]"},
        )
        payload = json.loads(response.content)

        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"], "No hay productos para guardar.")

    def test_post_save_products_with_invalid_json_returns_error(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {"action": "save_products", "store": "test_mock", "products": "{no-json"},
        )
        payload = json.loads(response.content)

        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"], "Formato de productos invalido.")

    def test_save_products_denied_for_user_without_permission(self):
        plain = User.objects.create_user(
            username="plain_user",
            email="plain@example.com",
            password="testpass123",
            dni="8888888888",
        )
        self.client.force_login(plain)

        response = self.client.post(
            self.url,
            {"action": "save_products", "store": "test_mock", "products": "[]"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Product.objects.count(), 0)

    def test_post_without_url_returns_error(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                "action": "scan",
                "store": "test_mock",
                "url": "",
                "max_products": "10",
            },
        )
        payload = json.loads(response.content)

        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"], "Ingrese una URL para escanear.")

    def test_post_with_invalid_max_products_returns_error(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                "action": "scan",
                "store": "test_mock",
                "url": "https://example.com/test/",
                "max_products": "abc",
            },
        )
        payload = json.loads(response.content)

        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"], "El maximo de productos debe ser un numero entero.")


class TestScraperSourceView(TestCase):
    def setUp(self):
        self.url = reverse("scraper_source_create")
        self.user = User.objects.create_superuser(
            username="source_admin",
            email="source@example.com",
            password="testpass123",
            dni="7777777777",
        )
        self.client.force_login(self.user)

    def test_create_accepts_multiple_urls_from_pasted_value(self):
        response = self.client.post(
            self.url,
            {
                "action": "add",
                "name": "etafashion MUJER BLUSA",
                "url": (
                    "https://www.etafashion.com/MUJERES/MODA-MUJER/BLUSAS/c/10105230599 "
                    "https://www.etafashion.com/HOMBRES/MODA-ADULTO/CAMISETAS-Y-POLOS/c/10202816499"
                ),
            },
        )

        payload = json.loads(response.content)

        self.assertTrue(payload["success"])
        self.assertEqual(payload["created"], 2)
        self.assertEqual(ScraperSource.objects.count(), 2)
        self.assertTrue(
            ScraperSource.objects.filter(
                url="https://www.etafashion.com/MUJERES/MODA-MUJER/BLUSAS/c/10105230599",
            ).exists()
        )
        self.assertTrue(
            ScraperSource.objects.filter(
                url="https://www.etafashion.com/HOMBRES/MODA-ADULTO/CAMISETAS-Y-POLOS/c/10202816499",
            ).exists()
        )
