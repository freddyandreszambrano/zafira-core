from django.test import SimpleTestCase

from core.scraper.extract import (
    extract_product,
    extract_products,
    looks_js_rendered,
    parse_price,
    slug_id,
)

JSONLD_PRODUCT_PAGE = """
<html><head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Vestido Midi Floral",
  "sku": "VM-778",
  "url": "https://tienda.io/producto/vestido-midi-floral",
  "image": ["https://tienda.io/img/vm778-1.jpg", "https://tienda.io/img/vm778-2.jpg"],
  "description": "Vestido midi con estampado floral.",
  "color": "Rojo",
  "offers": {"@type": "Offer", "price": "45.90", "priceCurrency": "USD",
             "availability": "https://schema.org/InStock"}
}
</script>
</head><body></body></html>
"""

JSONLD_ITEMLIST_PAGE = """
<html><head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1,
     "item": {"@type": "Product", "name": "Blusa Blanca", "url": "https://tienda.io/p/blusa-blanca",
              "image": "https://tienda.io/img/b1.jpg",
              "offers": {"@type": "Offer", "price": 19.99, "priceCurrency": "USD"}}},
    {"@type": "ListItem", "position": 2,
     "item": {"@type": "Product", "name": "Falda Plisada",
              "url": "https://tienda.io/p/falda-plisada",
              "image": "https://tienda.io/img/f1.jpg",
              "offers": {"@type": "Offer", "price": "29,90", "priceCurrency": "USD"}}}
  ]
}
</script>
</head><body></body></html>
"""

OPENGRAPH_PAGE = """
<html><head>
<meta property="og:type" content="product">
<meta property="og:title" content="Chaqueta Denim Oversize">
<meta property="og:url" content="https://otra-tienda.com/products/chaqueta-denim">
<meta property="og:image" content="https://otra-tienda.com/cdn/ch1.jpg">
<meta property="og:description" content="Chaqueta denim de corte oversize.">
<meta property="product:price:amount" content="59.90">
<meta property="product:price:currency" content="USD">
</head><body><h1>Chaqueta Denim Oversize</h1></body></html>
"""

MICRODATA_PAGE = """
<html><body>
<div itemscope itemtype="https://schema.org/Product">
    <span itemprop="name">Pantalon Cargo</span>
    <img itemprop="image" src="/img/cargo.jpg">
    <div itemscope itemtype="https://schema.org/Offer">
        <meta itemprop="price" content="35.50">
        <meta itemprop="priceCurrency" content="USD">
    </div>
    <span itemprop="price" content="35.50"></span>
</div>
</body></html>
"""

NEXT_DATA_PAGE = """
<html><body>
<script id="__NEXT_DATA__" type="application/json">
{"props": {"pageProps": {"products": [
  {"name": "Camiseta Basica", "price": 12.5, "url": "/p/camiseta-basica",
   "image": "https://spa-shop.io/img/cb.jpg"},
  {"name": "Short Deportivo", "price": "18.90", "url": "/p/short-deportivo",
   "image": "https://spa-shop.io/img/sd.jpg"}
]}}}
</script>
</body></html>
"""

HEURISTIC_GRID_PAGE = """
<html><body><div class="grid">
<div class="card"><a href="/item/polo-azul" title="Polo Azul">
    <img src="/img/p1.jpg" alt="Polo Azul"></a>
    <h3>Polo Azul</h3><span class="price">$15.99</span></div>
<div class="card"><a href="/item/polo-rojo" title="Polo Rojo">
    <img src="/img/p2.jpg" alt="Polo Rojo"></a>
    <h3>Polo Rojo</h3><span class="price">$16.99</span></div>
<div class="card"><a href="/item/polo-verde" title="Polo Verde">
    <img src="/img/p3.jpg" alt="Polo Verde"></a>
    <h3>Polo Verde</h3><s>$25.00</s><span class="price">$17.99</span></div>
</div></body></html>
"""

HEURISTIC_COUNT_PAGE = """
<html><body><div class="grid">
<div class="card"><a href="/item/vestido-a" title="Vestido A">
    <img src="/img/a.jpg" alt="Vestido A"></a>
    <h3>Vestido A</h3><span>USD 49.99</span><span>3 colores</span></div>
<div class="card"><a href="/item/vestido-b" title="Vestido B">
    <img src="/img/b.jpg" alt="Vestido B"></a>
    <h3>Vestido B</h3><span>USD 59.99</span><span>2 colores</span></div>
<div class="card"><a href="/item/vestido-c" title="Vestido C">
    <img src="/img/c.jpg" alt="Vestido C"></a>
    <h3>Vestido C</h3><span>USD 39.99</span><span>5 colores</span></div>
</div></body></html>
"""


class TestParsePrice(SimpleTestCase):
    def test_formats(self):
        self.assertEqual(parse_price("$45.99"), 45.99)
        self.assertEqual(parse_price("$71,92"), 71.92)
        self.assertEqual(parse_price("1.299,00"), 1299.0)
        self.assertEqual(parse_price("$1,299.00"), 1299.0)
        self.assertEqual(parse_price("12.999"), 12999.0)
        self.assertEqual(parse_price("USD 89"), 89.0)
        self.assertEqual(parse_price(49.9), 49.9)
        self.assertIsNone(parse_price("sin precio"))
        self.assertIsNone(parse_price(None))

    def test_unseparated_thousands_not_truncated(self):
        self.assertEqual(parse_price("1299.00"), 1299.0)
        self.assertEqual(parse_price("1050"), 1050.0)
        self.assertEqual(parse_price("12999"), 12999.0)
        self.assertEqual(parse_price("USD 1450"), 1450.0)


class TestSlugId(SimpleTestCase):
    def test_uses_full_path_slug(self):
        self.assertEqual(slug_id("https://x.io/p/vestido-midi-floral/"), "p-vestido-midi-floral")
        self.assertEqual(slug_id("https://x.io/producto/blusa.html"), "producto-blusa")

    def test_distinguishes_mid_path_ids(self):
        self.assertNotEqual(
            slug_id("https://x.io/p/123/vestido-negro"),
            slug_id("https://x.io/p/456/vestido-negro"),
        )

    def test_short_paths_fall_back_to_hash(self):
        self.assertEqual(len(slug_id("https://x.io/")), 12)


class TestExtractProduct(SimpleTestCase):
    def test_jsonld_product(self):
        product, strategies = extract_product(
            JSONLD_PRODUCT_PAGE, "https://tienda.io/producto/vestido-midi-floral"
        )

        self.assertEqual(product["name"], "Vestido Midi Floral")
        self.assertEqual(product["id"], "VM-778")
        self.assertEqual(product["price"], 45.9)
        self.assertEqual(product["currency"], "USD")
        self.assertEqual(product["availability"], "available")
        self.assertEqual(len(product["image_urls"]), 2)
        self.assertIn("json-ld", strategies)

    def test_opengraph_product(self):
        product, strategies = extract_product(
            OPENGRAPH_PAGE, "https://otra-tienda.com/products/chaqueta-denim"
        )

        self.assertEqual(product["name"], "Chaqueta Denim Oversize")
        self.assertEqual(product["price"], 59.9)
        self.assertEqual(product["image_urls"], ["https://otra-tienda.com/cdn/ch1.jpg"])
        self.assertIn("opengraph", strategies)

    def test_no_product_returns_empty(self):
        product, _ = extract_product("<html><body><p>Hola</p></body></html>", "https://x.io/")

        self.assertEqual(product, {})


class TestExtractProducts(SimpleTestCase):
    def test_jsonld_itemlist(self):
        products, strategies = extract_products(JSONLD_ITEMLIST_PAGE, "https://tienda.io/mujer")

        self.assertEqual(len(products), 2)
        self.assertEqual(products[0]["price"], 19.99)
        self.assertEqual(products[1]["price"], 29.9)
        self.assertIn("json-ld", strategies)

    def test_microdata(self):
        products, strategies = extract_products(MICRODATA_PAGE, "https://micro.io/ropa")

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["name"], "Pantalon Cargo")
        self.assertEqual(products[0]["price"], 35.5)
        self.assertIn("microdata", strategies)

    def test_embedded_next_data(self):
        products, strategies = extract_products(NEXT_DATA_PAGE, "https://spa-shop.io/catalogo")

        names = {product["name"] for product in products}
        self.assertEqual(names, {"Camiseta Basica", "Short Deportivo"})
        self.assertIn("embedded-json", strategies)
        self.assertTrue(all(p["url"].startswith("https://spa-shop.io/") for p in products))

    def test_heuristic_cards(self):
        products, strategies = extract_products(HEURISTIC_GRID_PAGE, "https://basic-shop.com/")

        self.assertEqual(len(products), 3)
        self.assertIn("heuristic", strategies)
        by_name = {product["name"]: product for product in products}
        self.assertEqual(by_name["Polo Azul"]["price"], 15.99)
        self.assertEqual(by_name["Polo Verde"]["price"], 17.99)
        self.assertEqual(by_name["Polo Verde"]["price_old"], 25.0)

    def test_heuristic_ignores_count_numbers(self):
        products, _ = extract_products(HEURISTIC_COUNT_PAGE, "https://count-shop.com/")

        by_name = {product["name"]: product for product in products}
        self.assertEqual(by_name["Vestido A"]["price"], 49.99)
        self.assertEqual(by_name["Vestido B"]["price"], 59.99)
        self.assertEqual(by_name["Vestido C"]["price"], 39.99)


class TestLooksJsRendered(SimpleTestCase):
    def test_shell_page(self):
        self.assertTrue(looks_js_rendered("<html><body><div id='app'></div></body></html>"))

    def test_link_rich_page(self):
        links = "".join(f"<a href='/x/{i}'>x</a>" for i in range(20))
        self.assertFalse(looks_js_rendered(f"<html><body>{links}</body></html>"))
