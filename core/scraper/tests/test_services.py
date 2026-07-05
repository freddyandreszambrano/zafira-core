from decimal import Decimal

from django.test import TestCase

from core.scraper.models import Product
from core.scraper.services import _derive_gender, infer_store_from_url, save_products, scan_url


class TestScanUrlService(TestCase):
    def test_product_url_parses_single_product(self):
        result = scan_url("test_mock", "https://example.com/p/MOCK001/", max_products=10)

        self.assertTrue(result["success"])
        self.assertEqual(result["metadata"]["mode"], "product")
        self.assertEqual(result["metadata"]["total_products"], 1)
        self.assertEqual(result["products"][0]["id"], "MOCK001")

    def test_category_url_respects_max_products(self):
        result = scan_url("test_mock", "https://example.com/test/", max_products=2)

        self.assertTrue(result["success"])
        self.assertEqual(result["metadata"]["mode"], "category")
        self.assertEqual(result["metadata"]["total_products"], 2)
        self.assertEqual([product["id"] for product in result["products"]], ["MOCK001", "MOCK002"])

    def test_root_url_scans_adapter_categories(self):
        result = scan_url("test_mock", "https://example.com/", max_products=2)

        self.assertTrue(result["success"])
        self.assertEqual(result["metadata"]["mode"], "store")
        self.assertEqual(result["metadata"]["total_products"], 2)

    def test_invalid_store_returns_controlled_error(self):
        result = scan_url("missing", "https://example.com/test/", max_products=10)

        self.assertFalse(result["success"])
        self.assertIn("Adaptador 'missing' no encontrado", result["error"])
        self.assertEqual(result["products"], [])

    def test_modarm_rejects_external_url(self):
        result = scan_url("modarm", "https://example.com/test/", max_products=10)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "La URL debe pertenecer a modarm.com.")

    def test_invalid_max_products_returns_controlled_error(self):
        result = scan_url("test_mock", "https://example.com/test/", max_products="abc")

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "El maximo de productos debe ser un numero entero.")

    def test_scan_without_persist_leaves_db_empty(self):
        result = scan_url("test_mock", "https://example.com/test/", max_products=2, persist=False)

        self.assertTrue(result["success"])
        self.assertFalse(result["metadata"]["persisted"])
        self.assertEqual(Product.objects.count(), 0)

    def test_scan_with_persist_saves_products(self):
        result = scan_url("test_mock", "https://example.com/test/", max_products=2, persist=True)

        self.assertTrue(result["success"])
        self.assertEqual(Product.objects.count(), 2)


class TestDeriveGender(TestCase):
    def test_women_not_classified_as_man(self):
        self.assertEqual(_derive_gender("Women Dresses", ""), "woman")
        self.assertEqual(_derive_gender("", "https://shop.com/products/women-midi-dress"), "woman")
        self.assertEqual(_derive_gender("Female Tops", ""), "woman")

    def test_men_classified_as_man(self):
        self.assertEqual(_derive_gender("", "https://x.com/products/mens-shirt"), "man")
        self.assertEqual(_derive_gender("Ropa de Hombre", ""), "man")

    def test_neutral_returns_empty(self):
        self.assertEqual(_derive_gender("Accesorios", ""), "")


class TestInferStore(TestCase):
    def test_known_domain_wins_over_generic(self):
        self.assertEqual(infer_store_from_url("https://www.modarm.com/CAMISAS/c/1"), "modarm")

    def test_unknown_domain_falls_back_to_generic(self):
        self.assertEqual(infer_store_from_url("https://tienda-nueva.io/vestidos"), "generic")

    def test_invalid_url_raises(self):
        with self.assertRaises(ValueError):
            infer_store_from_url("no-es-una-url")


class TestSaveProducts(TestCase):
    def _product(self, product_id="EXT-1", **overrides):
        product = {
            "id": product_id,
            "name": "Vestido Midi Negro",
            "category": "Mujer/Vestidos",
            "url": "https://tienda.io/p/vestido-midi",
            "price": 49.99,
            "price_old": 69.99,
            "currency": "USD",
            "sizes": ["S", "M"],
            "colors": ["Negro"],
            "description": "Vestido midi",
            "image_urls": ["https://tienda.io/img/1.jpg"],
            "availability": "available",
            "extracted_at": "2026-07-05T10:00:00+00:00",
        }
        product.update(overrides)
        return product

    def test_creates_and_updates_products(self):
        saved = save_products("tienda.io", [self._product()])
        self.assertEqual(saved, {"created": 1, "updated": 0, "skipped": 0})

        saved = save_products("tienda.io", [self._product(price=39.99)])
        self.assertEqual(saved, {"created": 0, "updated": 1, "skipped": 0})

        product = Product.objects.get(id_external="EXT-1")
        self.assertEqual(product.store, "tienda.io")
        self.assertEqual(float(product.price), 39.99)
        self.assertEqual(product.gender, "woman")
        self.assertEqual(product.base_name, "Vestido Midi")

    def test_skips_products_without_identity(self):
        saved = save_products("tienda.io", [self._product(), {"name": "sin id"}, {"id": "X2"}])

        self.assertEqual(saved, {"created": 1, "updated": 0, "skipped": 2})

    def test_same_id_different_stores_coexist(self):
        save_products(
            "tienda-a.com",
            [self._product(product_id="slug-x", url="https://tienda-a.com/p/slug-x")],
        )
        save_products(
            "tienda-b.com",
            [self._product(product_id="slug-x", url="https://tienda-b.com/p/slug-x")],
        )

        self.assertEqual(Product.objects.filter(id_external="slug-x").count(), 2)
        product_a = Product.objects.get(store="tienda-a.com", id_external="slug-x")
        self.assertEqual(product_a.url, "https://tienda-a.com/p/slug-x")

    def test_out_of_range_price_is_clamped(self):
        save_products("tienda.io", [self._product(price=1e20)])

        product = Product.objects.get(id_external="EXT-1")
        self.assertEqual(product.price, Decimal("0"))
        # La tabla sigue siendo legible (no InvalidOperation al leer).
        self.assertEqual(Product.objects.count(), 1)

    def test_non_http_url_is_dropped(self):
        save_products(
            "tienda.io",
            [self._product(url="javascript:alert(1)")],
        )

        self.assertEqual(Product.objects.get(id_external="EXT-1").url, "")

    def test_rejects_empty_payload(self):
        with self.assertRaises(ValueError):
            save_products("tienda.io", [])

    def test_rejects_missing_store(self):
        with self.assertRaises(ValueError):
            save_products("", [self._product()])

    def test_rejects_non_dict_items(self):
        with self.assertRaises(ValueError):
            save_products("tienda.io", ["no-un-dict"])
