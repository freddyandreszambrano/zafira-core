from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.auth.models import User
from core.auth.utils import APP_SOURCES_ZAFIRA


class UserFieldValidationApiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        app_source = request.headers.get("app-source")

        if app_source not in APP_SOURCES_ZAFIRA:
            return Response(
                {"message": "Invalid app source"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        field = request.data.get("field")
        value = request.data.get("value", "").strip()

        if not field or not value:
            return Response(
                {"exists": False},
                status=status.HTTP_200_OK,
            )

        if field == "username":
            exists = User.objects.filter(username__iexact=value).exists()
            message = "El nombre de usuario ya se encuentra registrado."

        elif field == "email":
            exists = User.objects.filter(email__iexact=value).exists()
            message = "Este correo electrónico ya está asociado a una cuenta."

        elif field == "dni":
            exists = User.objects.filter(dni=value).exists()
            message = "La cédula ingresada ya se encuentra registrada."

        else:
            return Response(
                {"message": "Campo inválido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "exists": exists,
                "message": message if exists else "",
            }
        )
