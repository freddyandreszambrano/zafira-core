import threading

from django.conf import settings

from core.tryon.task.tryon import generate_try_on_task


def dispatch_generate_try_on(job_id):
    if settings.TRYON_USE_CELERY:
        generate_try_on_task.delay(job_id)
    else:
        # Sin Celery: generar en un hilo para que el POST responda al instante
        # y la app haga polling del estado (igual que con Celery). Ejecutarlo
        # dentro del request excede el timeout HTTP con outfits de 2 prendas.
        threading.Thread(
            target=lambda: generate_try_on_task.apply(args=[job_id]),
            daemon=True,
        ).start()
