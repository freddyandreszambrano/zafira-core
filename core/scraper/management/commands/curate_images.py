"""Curaduría del catálogo tras un scrape.

Para cada producto:
1. Normaliza la categoría mixta FALDAS Y VESTIDOS (por si quedan filas viejas).
2. Verifica qué URLs de imagen responden de verdad (las tiendas rotan URLs).
3. Elige como imagen principal la foto de la PRENDA SOLA Y DE FRENTE:
   primero con Gemini Flash-Lite (entiende vistas frontal/espalda/lado;
   ~medio centavo por producto) y, si no hay GEMINI_API_KEY o falla, con
   detección de rostros local (OpenCV) como respaldo. El listado se ve
   específico y el try-on recibe la prenda limpia y bien orientada.
4. Con --delete-broken, elimina los productos sin ninguna imagen viva.

Uso:
    python manage.py curate_images [--store modarm] [--limit N]
                                   [--max-images 6] [--delete-broken] [--no-ai]
"""

import os
import re

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


def _get_gemini_client():
    """Cliente para clasificar fotos; None si no hay key (usa el respaldo)."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    from google import genai
    from google.genai import types as genai_types

    return genai.Client(api_key=key, http_options=genai_types.HttpOptions(timeout=20_000))


def _shrink_jpeg(image_bytes, max_side=512):
    """Miniatura JPEG para clasificar sin gastar tokens de más."""
    import cv2
    import numpy as np

    data = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        return None
    height, width = image.shape[:2]
    if max(height, width) > max_side:
        scale = max_side / max(height, width)
        image = cv2.resize(image, (int(width * scale), int(height * scale)))
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return encoded.tobytes() if ok else None


def _ai_front_garment_index(client, images_bytes):
    """Índice (0-based) de la mejor foto para mostrar/probar la prenda.

    Prioridad: A) la prenda SOLA vista de frente (plana, colgada o en maniquí
    invisible); B) si no existe, la mejor vista FRONTAL aunque la lleve un
    modelo — cualquiera de las dos es mejor referencia que una espalda o un
    lateral. None si Gemini no da respuesta útil (cae al respaldo OpenCV)."""
    from google.genai import types as genai_types

    parts = []
    for data in images_bytes:
        small = _shrink_jpeg(data)
        if small is None:
            return None
        parts.append(genai_types.Part.from_bytes(data=small, mime_type="image/jpeg"))
    prompt = (
        f"You are given {len(images_bytes)} product photos of the same clothing "
        f"item, numbered 1 to {len(images_bytes)} in order. Answer two "
        "questions:\n"
        "A = the number of the photo that shows ONLY the garment itself (no "
        "visible person or model; flat lay, hanging, or invisible/ghost "
        "mannequin views all qualify) seen from the FRONT. 0 if none.\n"
        "B = the number of the best FRONT view of the garment overall (worn "
        "by a model is fine). NEVER choose a back or side view. 0 if none.\n"
        "Answer in exactly this format: A=<number> B=<number>"
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite", contents=[*parts, prompt]
    )
    text = getattr(response, "text", "") or ""
    a_match = re.search(r"A\s*[=:]\s*(\d+)", text)
    b_match = re.search(r"B\s*[=:]\s*(\d+)", text)
    for match in (a_match, b_match):
        index = int(match.group(1)) if match else 0
        if 1 <= index <= len(images_bytes):
            return index - 1
    return None


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
        parser.add_argument(
            "--no-ai",
            action="store_true",
            help="No usar Gemini para elegir la foto (solo detección de rostros)",
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

        gemini = None if options["no_ai"] else _get_gemini_client()
        if gemini:
            self.stdout.write("Selección de foto: Gemini (frontal) + respaldo OpenCV")
        else:
            self.stdout.write("Selección de foto: detección de rostros (OpenCV)")

        stats = {
            "ok": 0,
            "reordered": 0,
            "ai_picked": 0,
            "cleaned_urls": 0,
            "deleted": 0,
            "recategorized": 0,
        }
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
            # Foto principal: la prenda sola y DE FRENTE (Gemini); respaldo:
            # la primera foto sin persona detectada (OpenCV)
            garment_only = None
            if gemini:
                try:
                    picked = _ai_front_garment_index(gemini, [d for _, d in alive])
                except Exception:
                    picked = None
                if picked is not None:
                    garment_only = alive[picked][0]
                    stats["ai_picked"] += 1
            if garment_only is None:
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
