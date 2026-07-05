import base64

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile

from core.tryon.models import TryOnJob
from core.tryon.services.zafira_ia_client import (
    ZafiraIaClient,
    ZafiraIaError,
    ZafiraIaUnavailable,
)

USER_FRIENDLY_ERROR = "No pudimos generar tu prueba virtual. Intenta nuevamente."


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
        mobile_profile = job.user.mobile_profile
        data = ZafiraIaClient().try_on(
            external_ref=str(job.id),
            person_image_url=settings.SITE_URL + mobile_profile.try_on_photo.url,
            garment_image_url=job.garment_image_url,
            garment_type=job.garment_type,
        )
        image_bytes = base64.b64decode(data["result_image_b64"])
        job.result_image.save(f"{job.id}.png", ContentFile(image_bytes), save=False)
        job.status = TryOnJob.Status.COMPLETED
        job.error_message = ""
        job.save()
    except ZafiraIaUnavailable as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=5 * (self.request.retries + 1))
        _mark_failed(job, USER_FRIENDLY_ERROR)
    except (ZafiraIaError, KeyError, ValueError):
        _mark_failed(job, USER_FRIENDLY_ERROR)


def _mark_failed(job, message):
    job.status = TryOnJob.Status.FAILED
    job.error_message = message
    job.save(update_fields=["status", "error_message", "updated_at"])
