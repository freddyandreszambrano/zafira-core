"""Curaduría del catálogo tras un scrape.

Para cada producto:
1. Normaliza la categoría mixta FALDAS Y VESTIDOS (por si quedan filas viejas).
2. Verifica qué URLs de imagen responden de verdad (las tiendas rotan URLs).
3. Elige como imagen principal la primera SIN persona detectada (la prenda
   sola o el modelo recortado): el listado se ve específico y el try-on de
   Gemini recibe la prenda limpia, con menos no-ops y menos artefactos.
4. Con --delete-broken, elimina los productos sin ninguna imagen viva.

Uso:
    python manage.py curate_images [--store modarm] [--limit N]
                                   [--max-images 6] [--delete-broken]
"""

from django.core.management.base import BaseCommand

import requests

from core.scraper.models import Product
from core.scraper.services import _normalize_category

_UA = {"User-Agent": "Mozilla/5.0"}
_IMAGE_MAGIC = (b"\xff\xd8", b"\x89PNG", b"GIF8", b"RIFF")
_MAX_BYTES = 8 * 1024 * 1024


def _download_image(url):
    """Bytes de la imagen o None si la URL está rota o no es una imagen."""
    try:
        response = requests.get(url, headers=_UA, timeout=8, stream=True)
        if response.status_code != 200:
            return None
        data = response.raw.read(_MAX_BYTES, decode_content=True)
    except requests.RequestException:
        return None
    if not data or not any(data.startswith(m) or b"WEBP" in data[:16] for m in _IMAGE_MAGIC):
        return None
    return data


class Command(BaseCommand):
    help = "Verifica imágenes, elige la foto de prenda sola y limpia el catálogo"

    def add_arguments(self, parser):
        parser.add_argument("--store", default=None, help="Solo esta tienda")
        parser.add_argument("--limit", type=int, default=None, help="Solo N productos (pruebas)")
        parser.add_argument(
            "--max-images", type=int, default=6, help="Cuántas imágenes revisar por producto"
        )
        parser.add_argument(
            "--delete-broken",
            action="store_true",
            help="Eliminar productos sin ninguna imagen viva",
        )

    def handle(self, *args, **options):
        # Import perezoso: opencv solo hace falta para este comando
        import cv2

        cascades = [
            cv2.CascadeClassifier(cv2.data.haarcascades + name)
            for name in ("haarcascade_frontalface_default.xml", "haarcascade_profileface.xml")
        ]

        def has_person(image_bytes):
            import numpy as np

            data = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
            if image is None:
                return True  # ilegible: no arriesgarse a elegirla como principal
            height, width = image.shape[:2]
            if max(height, width) > 900:
                scale = 900 / max(height, width)
                image = cv2.resize(image, (int(width * scale), int(height * scale)))
            image = cv2.equalizeHist(image)
            return any(
                len(c.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5, minSize=(36, 36)))
                for c in cascades
            )

        queryset = Product.objects.all().order_by("id")
        if options["store"]:
            queryset = queryset.filter(store=options["store"])
        if options["limit"]:
            queryset = queryset[: options["limit"]]

        stats = {"ok": 0, "reordered": 0, "cleaned_urls": 0, "deleted": 0, "recategorized": 0}
        total = queryset.count()

        for index, product in enumerate(queryset, start=1):
            changed = []

            category = _normalize_category(product.name, product.category)
            if category != product.category:
                product.category = category
                changed.append("category")
                stats["recategorized"] += 1

            alive = []  # (url, bytes) que respondieron
            for url in product.image_urls[: options["max_images"]]:
                data = _download_image(url)
                if data:
                    alive.append((url, data))
            if len(alive) != len(product.image_urls[: options["max_images"]]):
                stats["cleaned_urls"] += 1

            if not alive:
                if options["delete_broken"]:
                    product.delete()
                    stats["deleted"] += 1
                    self.stdout.write(f"[{index}/{total}] ELIMINADO (sin imagenes): {product.name}")
                    continue
                # Sin imágenes vivas y sin permiso de borrar: dejar tal cual
                if changed:
                    product.save(update_fields=changed)
                continue

            urls = [url for url, _ in alive]
            # La primera foto SIN persona pasa al frente (prenda sola)
            garment_only = next((url for url, data in alive if not has_person(data)), None)
            if garment_only and urls[0] != garment_only:
                urls.remove(garment_only)
                urls.insert(0, garment_only)
                stats["reordered"] += 1

            if urls != product.image_urls:
                product.image_urls = urls
                changed.append("image_urls")

            if changed:
                product.save(update_fields=changed)
            stats["ok"] += 1

            if index % 25 == 0:
                self.stdout.write(f"[{index}/{total}] procesados...")

        self.stdout.write(self.style.SUCCESS(f"Listo: {stats}"))
