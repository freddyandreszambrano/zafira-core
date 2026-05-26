from unittest.mock import MagicMock, Mock, patch
from django.test import SimpleTestCase
from bs4 import BeautifulSoup

from app.scraper.adapters.modarm import ModarmAdapter
from app.scraper import parsers


class TestModarmAdapterCategories(SimpleTestCase):
    """Test suite for ModarmAdapter.get_categories()."""

    def setUp(self):
        self.adapter = ModarmAdapter()

    def test_returns_list(self):
        """Test that get_categories returns a list."""
        result = self.adapter.get_categories()
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_has_required_fields(self):
        """Test that each category has required fields."""
        categories = self.adapter.get_categories()
        required_fields = {'name', 'path', 'url'}

        for category in categories:
            self.assertTrue(required_fields.issubset(category.keys()))

    def test_category_names_correct(self):
        """Test that category names match expected values."""
        categories = self.adapter.get_categories()
        category_names = [cat['name'] for cat in categories]

        expected_names = ['Mujeres', 'Hombres', 'Infantil', 'Calzado', 'Accesorios']
        self.assertEqual(category_names, expected_names)


class TestModarmAdapterScrapingCategory(SimpleTestCase):
    """Test suite for ModarmAdapter.scrape_category()."""

    def setUp(self):
        self.adapter = ModarmAdapter()

    @patch('app.scraper.adapters.modarm.requests.get')
    def test_scrape_category_returns_list(self, mock_get):
        """Test that scrape_category returns a list of products."""
        mock_response = Mock()
        mock_response.content = '''
            <html>
                <a href="/es_RW/p/123456/">Product 1</a>
                <a href="/es_RW/p/789012/">Product 2</a>
            </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        category = {
            'name': 'Test Category',
            'path': '/test/',
            'url': 'https://www.modarm.com/test/'
        }

        result = self.adapter.scrape_category(category)
        self.assertIsInstance(result, list)

    @patch('app.scraper.adapters.modarm.requests.get')
    def test_scrape_category_has_required_fields(self, mock_get):
        """Test that each product has required fields."""
        mock_response = Mock()
        mock_response.content = '''
            <html>
                <a href="/es_RW/p/123456/" data-product-name="Camisa Azul">Product</a>
            </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        category = {
            'name': 'Test',
            'path': '/test/',
            'url': 'https://www.modarm.com/test/'
        }

        products = self.adapter.scrape_category(category)
        required_fields = {'id', 'name', 'url'}

        for product in products:
            self.assertTrue(required_fields.issubset(product.keys()))


class TestModarmAdapterParseProduct(SimpleTestCase):
    """Test suite for ModarmAdapter.parse_product()."""

    def setUp(self):
        self.adapter = ModarmAdapter()

    @patch('app.scraper.adapters.modarm.requests.get')
    def test_parse_product_returns_dict(self, mock_get):
        """Test that parse_product returns a dictionary."""
        mock_response = Mock()
        mock_response.content = '<html><h1>Test Product</h1></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.adapter.parse_product('https://www.modarm.com/es_RW/p/123456/')
        self.assertIsInstance(result, dict)

    @patch('app.scraper.adapters.modarm.requests.get')
    def test_parse_product_extracts_id(self, mock_get):
        """Test that parse_product extracts product ID from URL."""
        mock_response = Mock()
        mock_response.content = '<html><h1>Test</h1></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.adapter.parse_product('https://www.modarm.com/es_RW/p/ABC123DEF/')
        self.assertEqual(result['id'], 'ABC123DEF')

    @patch('app.scraper.adapters.modarm.requests.get')
    def test_parse_product_normalizes_price(self, mock_get):
        """Test that parse_product normalizes price to float."""
        mock_response = Mock()
        mock_response.content = '''
            <html>
                <h1>Test Product</h1>
                <span class="price">$45.99</span>
            </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.adapter.parse_product('https://www.modarm.com/es_RW/p/123456/')
        self.assertEqual(result['price'], 45.99)
        self.assertIsInstance(result['price'], float)


class TestModarmAdapterHelpers(SimpleTestCase):
    """Test suite for ModarmAdapter helper methods."""

    def setUp(self):
        self.adapter = ModarmAdapter()

    def test_extract_product_id_with_trailing_slash(self):
        """Test _extract_product_id with trailing slash."""
        url = 'https://www.modarm.com/es_RW/p/123456/'
        result = self.adapter._extract_product_id(url)
        self.assertEqual(result, '123456')

    def test_extract_product_id_without_trailing_slash(self):
        """Test _extract_product_id without trailing slash."""
        url = 'https://www.modarm.com/es_RW/p/ABC789'
        result = self.adapter._extract_product_id(url)
        self.assertEqual(result, 'ABC789')

    def test_extract_product_id_with_query_params(self):
        """Test _extract_product_id with query parameters."""
        url = 'https://www.modarm.com/es_RW/p/XYZ123?color=blue&size=M'
        result = self.adapter._extract_product_id(url)
        self.assertEqual(result, 'XYZ123')
