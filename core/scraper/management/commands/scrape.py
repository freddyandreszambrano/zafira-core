import json

from django.core.management.base import BaseCommand, CommandError

from core.scraper.adapters import ADAPTER_MAP
from core.scraper.services import scan_store


class Command(BaseCommand):
    help = "Scrape de tienda (modarm por defecto)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--store",
            default="modarm",
            help="Nombre del adaptador (modarm, zara, etc.). Default: modarm",
        )
        parser.add_argument(
            "--max-products",
            type=int,
            default=None,
            help="Maximo de productos a extraer. Default: sin limite",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Output detallado",
        )

    def handle(self, *args, **options):
        store = options["store"]
        max_products = options["max_products"]
        verbose = options["verbose"]

        if store not in ADAPTER_MAP:
            raise CommandError(
                f"Adaptador '{store}' no encontrado. "
                f"Disponibles: {', '.join(ADAPTER_MAP.keys())}"
            )

        try:
            output = scan_store(store, max_products=max_products)
        except Exception as e:
            raise CommandError(str(e))

        print(json.dumps(output, indent=2, ensure_ascii=False))

        if verbose:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("[OK] Scraping complete"))
            self.stdout.write(f"    Total products: {output['metadata']['total_products']}")
            self.stdout.write(f"    Total errors: {output['metadata']['total_errors']}")
