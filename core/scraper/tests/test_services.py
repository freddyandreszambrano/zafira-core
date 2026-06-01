from django.test import SimpleTestCase

from core.scraper.services import scan_url


class TestScanUrlService(SimpleTestCase):
    def test_product_url_parses_single_product(self):
        result = scan_url('test_mock', 'https://example.com/p/MOCK001/', max_products=10)

        self.assertTrue(result['success'])
        self.assertEqual(result['metadata']['mode'], 'product')
        self.assertEqual(result['metadata']['total_products'], 1)
        self.assertEqual(result['products'][0]['id'], 'MOCK001')

    def test_category_url_respects_max_products(self):
        result = scan_url('test_mock', 'https://example.com/test/', max_products=2)

        self.assertTrue(result['success'])
        self.assertEqual(result['metadata']['mode'], 'category')
        self.assertEqual(result['metadata']['total_products'], 2)
        self.assertEqual([product['id'] for product in result['products']], ['MOCK001', 'MOCK002'])

    def test_invalid_store_returns_controlled_error(self):
        result = scan_url('missing', 'https://example.com/test/', max_products=10)

        self.assertFalse(result['success'])
        self.assertIn("Adaptador 'missing' no encontrado", result['error'])
        self.assertEqual(result['products'], [])

    def test_modarm_rejects_external_url(self):
        result = scan_url('modarm', 'https://example.com/test/', max_products=10)

        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'La URL debe pertenecer a modarm.com.')

    def test_invalid_max_products_returns_controlled_error(self):
        result = scan_url('test_mock', 'https://example.com/test/', max_products='abc')

        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'El maximo de productos debe ser un numero entero.')
