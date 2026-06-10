import json

from django.test import TestCase
from django.urls import reverse

from core.auth.models import User


class TestScraperScanView(TestCase):
    def setUp(self):
        self.url = reverse("scraper_scan")
        self.user = User.objects.create_user(
            username="scraper_user",
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
