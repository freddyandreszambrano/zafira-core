from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from core.scraper.adapters.modarm import ModarmAdapter


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
        required_fields = {"name", "path", "url"}

        for category in categories:
            self.assertTrue(required_fields.issubset(category.keys()))

    def test_category_names_correct(self):
        """Test that category names match expected values."""
        categories = self.adapter.get_categories()
        category_names = [cat["name"] for cat in categories]

        self.assertEqual(category_names, [cat["name"] for cat in ModarmAdapter.CATEGORIES])
        self.assertIn("Mujer - Vestidos", category_names)
        self.assertIn("Hombre - Camisas", category_names)


class TestModarmAdapterScrapingCategory(SimpleTestCase):
    """Test suite for ModarmAdapter.scrape_category()."""

    def setUp(self):
        self.adapter = ModarmAdapter()

    @patch.object(ModarmAdapter, "_fetch_category_html")
    def test_scrape_category_returns_list(self, mock_fetch):
        """Test that scrape_category returns a list of products."""
        mock_fetch.return_value = """
            <html>
                <a href="/es_RW/p/123456/">Product 1</a>
                <a href="/es_RW/p/789012/">Product 2</a>
            </html>
        """

        category = {
            "name": "Test Category",
            "path": "/test/",
            "url": "https://www.modarm.com/test/",
        }

        result = self.adapter.scrape_category(category)
        self.assertIsInstance(result, list)
        self.assertEqual([product["id"] for product in result], ["123456", "789012"])

    @patch.object(ModarmAdapter, "_fetch_category_html")
    def test_scrape_category_has_required_fields(self, mock_fetch):
        """Test that each product has required fields."""
        mock_fetch.return_value = """
            <html>
                <a href="/es_RW/p/123456/" data-product-name="Camisa Azul">Product</a>
            </html>
        """

        category = {"name": "Test", "path": "/test/", "url": "https://www.modarm.com/test/"}

        products = self.adapter.scrape_category(category)
        required_fields = {"id", "name", "url"}

        self.assertTrue(products)
        for product in products:
            self.assertTrue(required_fields.issubset(product.keys()))

    @patch.object(ModarmAdapter, "_fetch_category_html")
    def test_scrape_category_propagates_fetch_errors(self, mock_fetch):
        """El error debe subir a services para mostrarse en la UI, no tragarse."""
        mock_fetch.side_effect = RuntimeError("Executable doesn't exist")

        category = {"name": "Test", "path": "/test/", "url": "https://www.modarm.com/test/"}

        with self.assertRaises(RuntimeError):
            self.adapter.scrape_category(category)


class TestModarmAdapterParseProduct(SimpleTestCase):
    """Test suite for ModarmAdapter.parse_product()."""

    def setUp(self):
        self.adapter = ModarmAdapter()

    @patch("core.scraper.adapters.modarm.requests.get")
    def test_parse_product_returns_dict(self, mock_get):
        """Test that parse_product returns a dictionary."""
        mock_response = Mock()
        mock_response.content = "<html><h1>Test Product</h1></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.adapter.parse_product("https://www.modarm.com/es_RW/p/123456/")
        self.assertIsInstance(result, dict)

    @patch("core.scraper.adapters.modarm.requests.get")
    def test_parse_product_extracts_id(self, mock_get):
        """Test that parse_product extracts product ID from URL."""
        mock_response = Mock()
        mock_response.content = "<html><h1>Test</h1></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.adapter.parse_product("https://www.modarm.com/es_RW/p/ABC123DEF/")
        self.assertEqual(result["id"], "ABC123DEF")

    @patch("core.scraper.adapters.modarm.requests.get")
    def test_parse_product_normalizes_price(self, mock_get):
        """Test that parse_product normalizes price to float."""
        mock_response = Mock()
        mock_response.content = """
            <html>
                <h1>Test Product</h1>
                <span class="price">$45.99</span>
            </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.adapter.parse_product("https://www.modarm.com/es_RW/p/123456/")
        self.assertEqual(result["price"], 45.99)
        self.assertIsInstance(result["price"], float)

    @patch("core.scraper.adapters.modarm.requests.get")
    def test_parse_product_uses_modarm_name_when_cookie_banner_has_heading(self, mock_get):
        mock_response = Mock()
        mock_response.content = """
            <html>
                <h2>Antes de empezar a comprar</h2>
                <div class="product-details page-title">
                    <div class="name">
                        Abrigo Clásico Kaki
                        <span class="sku">ID</span>
                        <span class="code">005000001084198003</span>
                    </div>
                </div>
            </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.adapter.parse_product("https://www.modarm.com/es_RW/p/005000001084198003/")

        self.assertEqual(result["name"], "Abrigo Clásico Kaki")

    @patch("core.scraper.adapters.modarm.requests.get")
    def test_parse_product_extracts_modarm_discount_prices(self, mock_get):
        mock_response = Mock()
        mock_response.content = """
            <html>
                <div class="product-details price-panel">
                    <span class="priceDiscountDetails">$71,92</span>
                    <span class="priceOldDetails">$89,90</span>
                </div>
            </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.adapter.parse_product("https://www.modarm.com/es_RW/p/005000001084198003/")

        self.assertEqual(result["price"], 71.92)
        self.assertEqual(result["price_old"], 89.90)

    @patch("core.scraper.adapters.modarm.requests.get")
    def test_parse_product_extracts_modarm_regular_price(self, mock_get):
        mock_response = Mock()
        mock_response.content = """
            <html>
                <div class="product-details price-panel">
                    <div class="pdp-prices-box">
                        <div class="title">Tarjeta de crédito</div>
                        <div class="direct-credit-price">$79,90</div>
                    </div>
                </div>
            </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.adapter.parse_product("https://www.modarm.com/es_RW/p/005000001097713003/")

        self.assertEqual(result["price"], 79.90)
        self.assertIsNone(result["price_old"])

    @patch("core.scraper.adapters.modarm.requests.get")
    def test_parse_product_filters_non_product_images(self, mock_get):
        mock_response = Mock()
        mock_response.content = """
            <html>
                <img src="/medias/logo-rm.svg">
                <img src="/_ui/responsive/common/images/lupa_mas.svg">
                <img class="lazyOwl" data-src="/medias/000005000001084198-1200-1.webp?context=abc">
            </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.adapter.parse_product("https://www.modarm.com/es_RW/p/005000001084198003/")

        self.assertEqual(
            result["image_urls"],
            ["https://www.modarm.com/medias/000005000001084198-1200-1.webp?context=abc"],
        )


class TestModarmAdapterHelpers(SimpleTestCase):
    """Test suite for ModarmAdapter helper methods."""

    def setUp(self):
        self.adapter = ModarmAdapter()

    def test_extract_product_id_with_trailing_slash(self):
        """Test _extract_product_id with trailing slash."""
        url = "https://www.modarm.com/es_RW/p/123456/"
        result = self.adapter._extract_product_id(url)
        self.assertEqual(result, "123456")

    def test_extract_product_id_without_trailing_slash(self):
        """Test _extract_product_id without trailing slash."""
        url = "https://www.modarm.com/es_RW/p/ABC789"
        result = self.adapter._extract_product_id(url)
        self.assertEqual(result, "ABC789")

    def test_extract_product_id_with_query_params(self):
        """Test _extract_product_id with query parameters."""
        url = "https://www.modarm.com/es_RW/p/XYZ123?color=blue&size=M"
        result = self.adapter._extract_product_id(url)
        self.assertEqual(result, "XYZ123")


@override_settings(SCRAPER_USE_BROWSER=False)
class TestModarmAdapterLiteMode(SimpleTestCase):
    """Modo ligero (producción sin navegador): el scraper trabaja solo por
    HTTP para no lanzar Chromium, que en Render free tumba el servidor."""

    def setUp(self):
        self.adapter = ModarmAdapter()

    def test_use_browser_reads_setting(self):
        self.assertFalse(self.adapter.use_browser)

    def test_check_sizes_availability_skips_browser(self):
        """Devuelve las tallas del HTML sin abrir el navegador de stock."""
        size_options = [{"label": "S", "url": None}, {"label": "M", "url": "/talla-m"}]

        with patch.object(ModarmAdapter, "_check_sizes_availability_sync") as mock_sync:
            sizes = self.adapter._check_sizes_availability(size_options)

        mock_sync.assert_not_called()
        self.assertEqual(sizes, ["S", "M"])

    @patch("core.scraper.adapters.modarm.requests.get")
    def test_fetch_category_html_uses_http_not_browser(self, mock_get):
        """La lista de categoría sale del HTML estático, sin lanzar Chromium."""
        mock_response = Mock()
        mock_response.text = "<html><a href='/p/123456/'>Camisa</a></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch.object(ModarmAdapter, "_get_browser") as mock_browser:
            html = self.adapter._fetch_category_html("https://www.modarm.com/CAMISAS/c/1")

        mock_browser.assert_not_called()
        mock_get.assert_called_once()
        self.assertIn("/p/123456/", html)
