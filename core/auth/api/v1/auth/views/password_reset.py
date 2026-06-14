import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.auth.api.v1.auth.serializer.password_reset import (
    PasswordResetConfirmSerializerInput,
    PasswordResetRequestSerializerInput,
)
from core.auth.utils import APP_SOURCES_ZAFIRA
from core.auth.utils.email import send_password_reset_code_email

# Producción (Celery):
# from core.auth.tasks import send_password_reset_email_task

User = get_user_model()

CODE_TTL_MINUTES = 15


def _generate_code():
    return f"{secrets.randbelow(1000000):06d}"


class PasswordResetRequestApiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        app_source = request.headers.get("app-source")
        if app_source not in APP_SOURCES_ZAFIRA:
            return Response({"message": "Invalid app source"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PasswordResetRequestSerializerInput(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        # Respuesta genérica: no revelamos si el correo existe o no.
        generic = {
            "message": "Si el correo está registrado, te enviamos un código para restablecer tu contraseña."
        }

        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            return Response(generic, status=status.HTTP_200_OK)

        code = _generate_code()
        user.email_reset_token = make_password(code)
        user.email_reset_expires_at = timezone.now() + timedelta(minutes=CODE_TTL_MINUTES)
        user.password_reset_pending = True
        user.save(
            update_fields=[
                "email_reset_token",
                "email_reset_expires_at",
                "password_reset_pending",
            ]
        )

        # Modo prueba (sin Celery): envío directo.
        send_password_reset_code_email(user.email, user.get_full_name(), code)
        # Producción (Celery):
        # send_password_reset_email_task.delay(user.email, user.get_full_name(), code)

        return Response(generic, status=status.HTTP_200_OK)


class PasswordResetConfirmApiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        app_source = request.headers.get("app-source")
        if app_source not in APP_SOURCES_ZAFIRA:
            return Response({"message": "Invalid app source"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PasswordResetConfirmSerializerInput(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = User.objects.filter(email__iexact=data["email"]).first()

        invalid = {"message": "El código es inválido o ha expirado."}
        if user is None or not user.password_reset_pending or not user.email_reset_token:
            return Response(invalid, status=status.HTTP_400_BAD_REQUEST)
        if not user.email_reset_expires_at or user.email_reset_expires_at < timezone.now():
            return Response(invalid, status=status.HTTP_400_BAD_REQUEST)
        if not check_password(data["code"], user.email_reset_token):
            return Response(invalid, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(data["password"])
        user.email_reset_token = None
        user.email_reset_expires_at = None
        user.password_reset_pending = False
        user.password_reset_count = (user.password_reset_count or 0) + 1
        user.last_password_reset_at = timezone.now()
        user.save(
            update_fields=[
                "password",
                "email_reset_token",
                "email_reset_expires_at",
                "password_reset_pending",
                "password_reset_count",
                "last_password_reset_at",
                "last_password_change_at",
            ]
        )

        return Response(
            {"message": "Contraseña actualizada correctamente."},
            status=status.HTTP_200_OK,
        )
