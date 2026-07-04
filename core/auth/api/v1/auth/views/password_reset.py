from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.auth.api.v1.auth.features import PasswordResetApi
from core.auth.api.v1.auth.outputs import MessageOutput
from core.auth.api.v1.auth.serializer.password_reset import (
    PasswordResetConfirmSerializerInput,
    PasswordResetRequestSerializerInput,
)
from core.auth.utils import APP_SOURCES_ZAFIRA


class PasswordResetRequestApiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        app_source = request.headers.get("app-source")
        if app_source not in APP_SOURCES_ZAFIRA:
            return Response(MessageOutput("Invalid app source").data, status=status.HTTP_400_BAD_REQUEST)

        serializer = PasswordResetRequestSerializerInput(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        try:
            user = PasswordResetApi().request_reset(email)
        except Exception:
            return Response(
                MessageOutput(
                    "No pudimos enviar el codigo en este momento. "
                    "Verifica la configuracion del correo e intentalo nuevamente."
                ).data,
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if user is None:
            return Response(
                MessageOutput(
                    "No encontramos una cuenta asociada a este correo electronico. "
                    "Verifica la direccion e intentalo nuevamente."
                ).data,
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            MessageOutput("Hemos enviado un codigo de verificacion a tu correo electronico.").data,
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmApiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        app_source = request.headers.get("app-source")
        if app_source not in APP_SOURCES_ZAFIRA:
            return Response(MessageOutput("Invalid app source").data, status=status.HTTP_400_BAD_REQUEST)

        serializer = PasswordResetConfirmSerializerInput(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        confirmed = PasswordResetApi().confirm_reset(data["email"], data["code"], data["password"])
        if not confirmed:
            return Response(
                MessageOutput(PasswordResetApi.invalid_code_message).data,
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            MessageOutput("Contrasena actualizada correctamente.").data,
            status=status.HTTP_200_OK,
        )
