from django.conf import settings

from core.tryon.task.tryon import generate_try_on_task


def dispatch_generate_try_on(job_id):
    if settings.TRYON_USE_CELERY:
        generate_try_on_task.delay(job_id)
    else:
        generate_try_on_task.apply(args=[job_id])
