import logging

from django.db import models
from django.forms import model_to_dict
from django.utils import timezone

from config.settings import ECUADOR_TZ


def save_error_app(name, e):
    if e is str:
        logging.error(e)
        message = e
    else:
        logging.exception(e)
        message = str(e)
    queryset = ErrorApp.objects.filter(name=name, error=message)
    if not queryset.exists():
        ErrorApp.objects.create(name=name, error=message)
    else:
        queryset.update(date_joined=timezone.now())
    return ""


class ErrorApp(models.Model):
    name = models.TextField(blank=True, null=True)
    date_joined = models.DateTimeField(auto_now=True)
    error = models.TextField(blank=True, null=True)

    def to_json(self):
        item = model_to_dict(self)
        item["date_joined"] = self.date_joined.astimezone(ECUADOR_TZ).strftime("%Y-%m-%d %H:%M:%S")
        return item

    class Meta:
        verbose_name = "Error de aplicación"
        verbose_name_plural = "Errores de aplicaciones"
        default_permissions = ()
        permissions = (
            ("view_errorapp", "Can view Error de aplicación"),
            ("delete_errorapp", "Can delete Error de aplicación"),
        )
        ordering = ["-id"]
