import json
from django.core.management.base import BaseCommand, CommandError
from app.scraper.adapters import ADAPTER_MAP
from app.scraper import parsers


class Command(BaseCommand):
    help = 'Scrape de tienda (modarm por defecto)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--store',
            default='modarm',
            help='Nombre del adaptador (modarm, zara, etc.). Default: modarm'
        )
        parser.add_argument(
            '--max-products',
            type=int,
            default=None,
            help='Máximo de productos a extraer. Default: sin límite'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Output detallado'
        )

    def handle(self, *args, **options):
        store = options['store']
        max_products = options['max_products']
        verbose = options['verbose']

        # 1. Validar que el adaptador exista
        if store not in ADAPTER_MAP:
            raise CommandError(
                f"Adaptador '{store}' no encontrado. "
                f"Disponibles: {', '.join(ADAPTER_MAP.keys())}"
            )

        # 2. Instanciar adaptador
        try:
            adapter = ADAPTER_MAP[store]()
        except Exception as e:
            raise CommandError(f"Error instanciando adaptador {store}: {e}")

        # 3. Diccionario para deduplicar por ID
        products = {}  # {id: producto}
        errors = []

        # 4. Iterar categorías
        categories = adapter.get_categories()

        for category in categories:
            if verbose:
                self.stdout.write(f"[*] Scraping {category['name']}...")

            try:
                # 5. Scrape de categoría → lista de producto links
                category_products = adapter.scrape_category(category)

                if verbose:
                    self.stdout.write(
                        f"    [+] Found {len(category_products)} product links"
                    )

                # 6. Para cada producto, parsear
                for i, prod_link in enumerate(category_products):
                    if max_products and len(products) >= max_products:
                        if verbose:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"    [!] Reached max_products limit ({max_products})"
                                )
                            )
                        break

                    try:
                        if verbose:
                            self.stdout.write(
                                f"    [-] [{i+1}/{len(category_products)}] Parsing {prod_link['id']}...",
                                ending=''
                            )

                        # 7. Parse producto
                        product = adapter.parse_product(prod_link['url'])
                        products[product['id']] = product

                        if verbose:
                            self.stdout.write(" [OK]")

                    except Exception as e:
                        error_msg = f"{prod_link.get('id', 'unknown')}: {str(e)}"
                        errors.append(error_msg)
                        if verbose:
                            self.stdout.write(
                                self.style.WARNING(f" [ERROR: {e}]"),
                                self.style.WARNING
                            )
                        # Fail-fast: continúa con el siguiente
                        continue

            except Exception as e:
                error_msg = f"{category['name']}: {str(e)}"
                errors.append(error_msg)
                if verbose:
                    self.stdout.write(
                        self.style.WARNING(f"    [ERROR] Error scraping category: {e}")
                    )
                # Continúa con la siguiente categoría
                continue

        # 8. Construir salida JSON
        output = {
            'metadata': {
                'store': store,
                'scraped_at': parsers.now_iso(),
                'total_products': len(products),
                'total_categories': len(categories),
                'total_errors': len(errors),
            },
            'products': list(products.values()),
            'errors': errors if errors else None,
        }

        # 9. Print JSON a stdout
        print(json.dumps(output, indent=2, ensure_ascii=False))

        # 10. Summary en stderr (no contamina JSON en stdout)
        if verbose:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('[OK] Scraping complete'))
            self.stdout.write(f'    Total products: {len(products)}')
            self.stdout.write(f'    Total errors: {len(errors)}')
