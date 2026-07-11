import os
from pathlib import Path

from django.apps import AppConfig
from django.conf import settings

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def discover_async_task_modules():
    task_modules = []
    for app_entry in settings.INSTALLED_APPS:
        app_config = AppConfig.create(app_entry)
        task_dir = Path(app_config.path) / "task"
        if not task_dir.exists():
            continue
        for task_file in task_dir.rglob("*.py"):
            if task_file.name == "__init__.py":
                continue
            relative_module = task_file.relative_to(task_dir).with_suffix("")
            module_parts = ".".join(relative_module.parts)
            task_modules.append(f"{app_config.name}.task.{module_parts}")
    return task_modules


ASYNC_TASK_MODULES = discover_async_task_modules()

PERIODIC_TASKS = {
    # Ejemplo:
    # "scraper-saved-sources-daily": {
    #     "task": "core.scraper.task.scraper.run.run_saved_sources_scraper_task",
    #     "schedule": crontab(hour=2, minute=0),
    #     "args": (50,),
    # },
}

app = Celery("core", include=ASYNC_TASK_MODULES)

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.beat_schedule = PERIODIC_TASKS
app.conf.timezone = settings.CELERY_TIMEZONE

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
