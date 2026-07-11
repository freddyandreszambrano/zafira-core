from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.auth.utils import APP_SOURCES_ZAFIRA
from core.user.api.v1.user.features import UserApi
from core.user.api.v1.user.outputs import FieldValidationOutput, MessageOutput


class UserFieldValidationApiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        app_source = request.headers.get("app-source")
        if app_source not in APP_SOURCES_ZAFIRA:
            return Response(
                MessageOutput("Invalid app source").data, status=status.HTTP_400_BAD_REQUEST
            )

        field = request.data.get("field")
        value = request.data.get("value", "").strip()

        if not field or not value:
            return Response(FieldValidationOutput().data, status=status.HTTP_200_OK)

        data = UserApi().validate_field(field, value)
        if data is None:
            return Response(
                MessageOutput("Campo invalido").data, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(FieldValidationOutput(**data).data)
