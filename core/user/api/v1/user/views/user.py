from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.auth.utils import APP_SOURCES_ZAFIRA
from core.common.error import save_error_api
from core.user.api.v1.user.features import UserApi
from core.user.api.v1.user.outputs import MessageOutput


class UserCreateApiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        app_source = request.headers.get("app-source")
        if app_source not in APP_SOURCES_ZAFIRA:
            return Response(MessageOutput("Invalid app source").data, status=status.HTTP_400_BAD_REQUEST)

        try:
            UserApi().create_user(request.data)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return save_error_api(request, e)

        return Response(status=status.HTTP_201_CREATED)
