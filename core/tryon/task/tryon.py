import base64
from urllib.parse import urljoin

from django.conf import settings
from django.core.files.base import ContentFile

from celery import shared_task

from core.tryon.models import TryOnJob
from core.tryon.services.zafira_ia_client import (
    ZafiraIaClient,
    ZafiraIaError,
    ZafiraIaRejected,
    ZafiraIaUnavailable,
)

GENERIC_ERROR = "No pudimos generar tu prueba virtual. Intenta nuevamente."
QUOTA_ERROR = "El servicio de IA no tiene cuota disponible ahora mismo. Intenta más tarde."
CONTENT_ERROR = "No pudimos generar la prueba con esta foto o prenda. Prueba con otra imagen."

# Outfit: cuantas veces intentar el paso 2 (piernas) si no se aplica la prenda.
# El usuario ya comprobó que reintentar el mismo outfit lo resuelve; esto lo
# automatiza. 2 = intento original + 1 reintento (acota el costo por generación).
_OUTFIT_LEGS_MAX_ATTEMPTS = 2
# Diferencia media de píxeles (gris, 64x64) por debajo de la cual la salida del
# paso 2 es casi idéntica al paso 1: la segunda prenda no se aplicó (no-op).
_OUTFIT_LEGS_NOOP_THRESHOLD = 3.0


def _mean_diff(a, b):
    """Diferencia media de píxeles (0-255) entre dos imágenes reducidas a 64x64
    en gris. ~0 = casi idénticas (la prenda del paso 2 no se aplicó)."""
    from io import BytesIO

    from PIL import Image

    def thumb(data):
        return Image.open(BytesIO(data)).convert("L").resize((64, 64))

    try:
        ia, ib = thumb(a), thumb(b)
    except Exception:
        return 255.0  # si no se puede comparar, asumir que cambió (no reintentar)
    pa, pb = ia.load(), ib.load()
    total = sum(abs(pa[x, y] - pb[x, y]) for x in range(64) for y in range(64))
    return total / (64 * 64)


@shared_task(bind=True, max_retries=2)
def generate_try_on_task(self, job_id):
    job = (
        TryOnJob.objects.select_related("user", "product")
        .filter(id=job_id)
        .exclude(status=TryOnJob.Status.COMPLETED)
        .first()
    )
    if not job:
        return

    job.status = TryOnJob.Status.PROCESSING
    job.save(update_fields=["status", "updated_at"])

    try:
        client = ZafiraIaClient()
        mobile_profile = job.user.mobile_profile
        person_image_url = urljoin(
            settings.SITE_URL.rstrip("/") + "/", mobile_profile.try_on_photo.url
        )

        # Outfit en UNA generación (~12-18s, mitad de costo). Si Gemini la
        # rechaza, sigue el encadenado clásico de 2 pasos como respaldo.
        if job.extra_garment_image_url and settings.TRYON_OUTFIT_SINGLE_CALL:
            if _single_call_outfit(client, job, person_image_url):
                job.status = TryOnJob.Status.COMPLETED
                job.error_message = ""
                job.save()
                return

        # Paso 1: vestir la primera prenda (torso) sobre la foto del usuario
        data = client.try_on(
            external_ref=str(job.id),
            person_image_url=person_image_url,
            garment_image_url=job.garment_image_url,
            garment_type=job.garment_type,
            # El nombre real de la prenda enfoca al modelo de try-on en la
            # prenda y reduce que copie rasgos del modelo de la tienda
            params={"garment_des": job.product.name},
        )
        image_bytes = base64.b64decode(data["result_image_b64"])
        job.result_image.save(f"{job.id}.png", ContentFile(image_bytes), save=True)

        # Paso 2 (solo outfit): vestir la segunda prenda (piernas) sobre el
        # resultado del paso 1, que ya tiene URL publica en /media/.
        # Cada intento parte SIEMPRE del paso 1 limpio (torso vestido). Solo se
        # acepta el resultado si de verdad aplicó la prenda de piernas: si la
        # salida es casi idéntica al paso 1 (no-op), se reintenta. Si ningún
        # intento aplica —o hay error de servicio— se CONSERVA el paso 1 (el
        # usuario ve el torso bien puesto en vez de romper todo el outfit).
        if job.extra_garment_image_url:
            step1_bytes = image_bytes
            for _ in range(_OUTFIT_LEGS_MAX_ATTEMPTS):
                try:
                    data = client.try_on(
                        external_ref=f"{job.id}-outfit",
                        person_image_url=settings.SITE_URL + job.result_image.url,
                        garment_image_url=job.extra_garment_image_url,
                        garment_type=job.extra_garment_type or "lower_body",
                        # El nombre enfoca a la IA en la prenda de piernas y
                        # reduce el no-op del paso 2.
                        params={"garment_des": job.extra_garment_name},
                    )
                    candidate = base64.b64decode(data["result_image_b64"])
                except (ZafiraIaError, KeyError, ValueError):
                    break  # error de servicio: conservar el paso 1 (torso)
                if _mean_diff(candidate, step1_bytes) >= _OUTFIT_LEGS_NOOP_THRESHOLD:
                    job.result_image.save(f"{job.id}.png", ContentFile(candidate), save=True)
                    break
                # no-op: la prenda de piernas no se aplicó, reintentar

        job.status = TryOnJob.Status.COMPLETED
        job.error_message = ""
        job.save()
    except ZafiraIaUnavailable as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=5 * (self.request.retries + 1))
        _mark_failed(job, QUOTA_ERROR if exc.code == "RATE_LIMITED" else GENERIC_ERROR)
    except ZafiraIaRejected as exc:
        _mark_failed(job, CONTENT_ERROR if exc.code == "GENERATION_REJECTED" else GENERIC_ERROR)
    except (ZafiraIaError, KeyError, ValueError):
        _mark_failed(job, GENERIC_ERROR)


def _single_call_outfit(client, job, person_image_url):
    """Outfit completo en una sola generación. True si el resultado quedó
    guardado; False para caer al encadenado de 2 pasos. Los errores de
    cuota/caída se propagan: el respaldo también fallaría y solo duplicaría
    llamadas (y costo)."""
    try:
        data = client.try_on(
            external_ref=str(job.id),
            person_image_url=person_image_url,
            garment_image_url=job.garment_image_url,
            garment_type=job.garment_type,
            extra_garment_image_url=job.extra_garment_image_url,
            extra_garment_type=job.extra_garment_type or "lower_body",
            params={
                "garment_des": job.product.name,
                "extra_garment_des": job.extra_garment_name,
            },
        )
        image_bytes = base64.b64decode(data["result_image_b64"])
    except ZafiraIaUnavailable:
        raise
    except (ZafiraIaError, KeyError, ValueError):
        return False
    job.result_image.save(f"{job.id}.png", ContentFile(image_bytes), save=True)
    return True


def _mark_failed(job, message):
    job.status = TryOnJob.Status.FAILED
    job.error_message = message
    job.save(update_fields=["status", "error_message", "updated_at"])
