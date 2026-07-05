from unittest.mock import Mock, patch

from django.test import TestCase

from core.scraper.adapters.generic import GenericAdapter
from core.scraper.models import Product
from core.scraper.services import scan_auto_url

LISTING_PAGE = """
<html><head>
<script type="application/ld+json">
{"@type": "ItemList", "itemListElement": [
  {"@type": "ListItem", "item": {"@type": "Product", "name": "Blusa Blanca",
   "url": "https://tienda-nueva.io/p/blusa-blanca", "image": "https://tienda-nueva.io/img/b1.jpg",
   "offers": {"price": 19.99, "priceCurrency": "USD"}}},
  {"@type": "ListItem", "item": {"@type": "Product", "name": "Falda Plisada",
   "url": "https://tienda-nueva.io/p/falda-plisada", "image": "https://tienda-nueva.io/img/f1.jpg",
   "offers": {"price": 29.90, "priceCurrency": "USD"}}}
]}
</script>
</head><body></body></html>
"""

PRODUCT_PAGE = """
<html><head>
<meta property="og:type" content="product">
<meta property="og:title" content="Chaqueta Denim">
<meta property="og:image" content="https://tienda-nueva.io/cdn/ch1.jpg">
<meta property="product:price:amount" content="59.90">
</head><body></body></html>
"""

LISTING_NO_OFFERS_PAGE = """
<html><head>
<script type="application/ld+json">
{"@type": "ItemList", "itemListElement": [
  {"@type": "ListItem", "item": {"@type": "Product", "name": "Vestido Largo Azul",
   "url": "https://tienda-nueva.io/vestido-largo-azul"}},
  {"@type": "ListItem", "item": {"@type": "Product", "name": "Falda Corta Roja",
   "url": "https://tienda-nueva.io/falda-corta-roja"}}
]}
</script>
</head><body></body></html>
"""

SHOPIFY_PAYLOAD = {
    "products": [
        {
            "id": 991,
            "title": "Hoodie Oversize",
            "handle": "hoodie-oversize",
            "body_html": "<p>Hoodie unisex</p>",
            "product_type": "Hoodies",
            "options": [
                {"name": "Size", "values": ["S", "M", "L"]},
                {"name": "Color", "values": ["Negro", "Gris"]},
            ],
            "variants": [{"price": "39.90", "compare_at_price": "49.90", "available": True}],
            "images": [{"src": "https://cdn.shopify.com/hoodie.jpg"}],
        }
    ]
}


def _response(status_code=200, text="", payload=None):
    response = Mock()
    response.status_code = status_code
    response.text = text
    response.json = Mock(
        side_effect=(lambda: payload) if payload is not None else ValueError("no json")
    )
    response.raise_for_status = Mock()
    return response


class TestGenericAdapter(TestCase):
    def setUp(self):
        self.adapter = GenericAdapter()

    def test_supports_any_http_url(self):
        self.assertTrue(GenericAdapter.supports_url("https://loquesea.com/ropa"))
        self.assertFalse(GenericAdapter.supports_url("ftp://loquesea.com"))
        self.assertFalse(GenericAdapter.supports_url("no-url"))

    @patch("core.scraper.adapters.generic.requests.get")
    def test_listing_with_jsonld_prefetches_products(self, mock_get):
        mock_get.side_effect = [
            _response(404),
            _response(200, LISTING_PAGE),
        ]

        links = self.adapter.scrape_category({"name": "x", "url": "https://tienda-nueva.io/mujer"})

        self.assertEqual(len(links), 2)
        self.assertEqual(links[0]["id"], "p-blusa-blanca")

        product = self.adapter.parse_product(links[0]["url"])
        self.assertEqual(product["name"], "Blusa Blanca")
        self.assertEqual(product["price"], 19.99)
        # prefetch: solo 2 requests (shopify probe + listado), ninguna por producto
        self.assertEqual(mock_get.call_count, 2)

    @patch("core.scraper.adapters.generic.requests.get")
    def test_listing_without_offers_still_yields_links(self, mock_get):
        mock_get.side_effect = [
            _response(404),
            _response(200, LISTING_NO_OFFERS_PAGE),
        ]

        links = self.adapter.scrape_category({"name": "x", "url": "https://tienda-nueva.io/mujer"})

        urls = {link["url"] for link in links}
        self.assertIn("https://tienda-nueva.io/vestido-largo-azul", urls)
        self.assertIn("https://tienda-nueva.io/falda-corta-roja", urls)

    @patch("core.scraper.adapters.generic.requests.get")
    def test_product_page_detected_as_single(self, mock_get):
        mock_get.side_effect = [
            _response(404),
            _response(200, PRODUCT_PAGE),
        ]

        links = self.adapter.scrape_category(
            {"name": "x", "url": "https://tienda-nueva.io/chaqueta-denim"}
        )

        self.assertEqual(len(links), 1)
        product = self.adapter.parse_product(links[0]["url"])
        self.assertEqual(product["name"], "Chaqueta Denim")
        self.assertEqual(product["price"], 59.9)

    @patch("core.scraper.adapters.generic.requests.get")
    def test_shopify_products_json_shortcut(self, mock_get):
        mock_get.return_value = _response(200, payload=SHOPIFY_PAYLOAD)

        links = self.adapter.scrape_category(
            {"name": "x", "url": "https://shopi-store.com/collections/all"}
        )

        self.assertEqual(self.adapter.last_strategies, ["shopify"])
        self.assertEqual(len(links), 1)

        product = self.adapter.parse_product(links[0]["url"])
        self.assertEqual(product["name"], "Hoodie Oversize")
        self.assertEqual(product["price"], 39.9)
        self.assertEqual(product["price_old"], 49.9)
        self.assertEqual(product["sizes"], ["S", "M", "L"])
        self.assertEqual(product["colors"], ["Negro", "Gris"])
        self.assertNotIn("<p>", product["description"])


class TestGenericEndToEnd(TestCase):
    @patch("core.scraper.adapters.generic.requests.get")
    def test_scan_auto_url_unknown_domain_saves_with_domain_store(self, mock_get):
        mock_get.side_effect = [
            _response(404),
            _response(200, LISTING_PAGE),
        ]

        result = scan_auto_url("https://tienda-nueva.io/mujer", max_products=5, persist=True)

        self.assertTrue(result["success"])
        self.assertEqual(result["metadata"]["store"], "tienda-nueva.io")
        self.assertEqual(result["metadata"]["total_products"], 2)
        self.assertIn("json-ld", result["metadata"]["strategies"])

        stores = set(Product.objects.values_list("store", flat=True))
        self.assertEqual(stores, {"tienda-nueva.io"})
        self.assertEqual(Product.objects.count(), 2)
