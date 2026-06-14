import logging

from crum import get_current_request
from django.db import models
from django.forms import model_to_dict
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from config.settings import ECUADOR_TZ
from core.auth.models import User
from core.common.utils.microserver.log_rest_api import ZafiraLogging


def save_error_api(request, e):
    if e is str:
        logging.error(e)
        message = e
    else:
        logging.exception(e)
        message = str(e)
    back_log = ZafiraLogging(request)
    back_log.change_status(status.HTTP_409_CONFLICT)
    back_log.change_message(message)
    back_log.print()
    path = f"{request.method} {request.path}"

    if not request.user.is_authenticated:
        queryset = ErrorApi.objects.filter(content=message, path=path)
        if not queryset.exists():
            ErrorApi(content=message, path=path).save()
        else:
            queryset.update(date_joined=timezone.now())
    else:
        queryset = ErrorApi.objects.filter(content=message, path=path, user=request.user)
        if not queryset.exists():
            ErrorApi.objects.create(content=message, path=path, user=request.user)
        else:
            queryset.update(date_joined=timezone.now())
    return Response({"message": message}, status=status.HTTP_409_CONFLICT)


class ErrorApi(models.Model):
    path = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    date_joined = models.DateTimeField(auto_now=True)
    content = models.TextField(blank=True, null=True)

    def to_json(self):
        item = model_to_dict(self)
        item["user"] = {} if self.user is None else self.user.to_json()
        item["date_joined"] = self.date_joined.astimezone(ECUADOR_TZ).strftime("%Y-%m-%d %H:%M:%S")
        return item

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        request = get_current_request()
        if request.user.is_authenticated:
            self.user = request.user
        super(ErrorApi, self).save()

    class Meta:
        verbose_name = "ErrorApi"
        verbose_name_plural = "ErrorApis"
        default_permissions = ()
        permissions = (
            ("view_errorapi", "Can view ErrorApi"),
            ("delete_errorapi", "Can delete ErrorApi"),
        )
        ordering = ["-id"]
