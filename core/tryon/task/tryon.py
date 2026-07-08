import base64

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile

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

        # Paso 1: vestir la primera prenda (torso) sobre la foto del usuario
        data = client.try_on(
            external_ref=str(job.id),
            person_image_url=settings.SITE_URL + mobile_profile.try_on_photo.url,
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
        # Si este paso falla, se CONSERVA el resultado del paso 1 (torso ya
        # puesto) en vez de romper todo el outfit: el usuario ve la prenda de
        # arriba bien y puede reintentar.
        if job.extra_garment_image_url:
            try:
                data = client.try_on(
                    external_ref=f"{job.id}-outfit",
                    person_image_url=settings.SITE_URL + job.result_image.url,
                    garment_image_url=job.extra_garment_image_url,
                    garment_type=job.extra_garment_type or "lower_body",
                )
                image_bytes = base64.b64decode(data["result_image_b64"])
                job.result_image.save(f"{job.id}.png", ContentFile(image_bytes), save=True)
            except (ZafiraIaError, KeyError, ValueError):
                # Paso 2 fallo: nos quedamos con el paso 1 (torso vestido)
                pass

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


def _mark_failed(job, message):
    job.status = TryOnJob.Status.FAILED
    job.error_message = message
    job.save(update_fields=["status", "error_message", "updated_at"])
