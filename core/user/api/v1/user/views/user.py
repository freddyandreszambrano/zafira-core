from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.auth.utils import APP_SOURCES_ZAFIRA
from core.common.error import save_error_api
from core.user.api.v1.user.serializer.user import UserCreateSerializerInput


class UserCreateApiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        app_source = request.headers.get("app-source")
        if app_source not in APP_SOURCES_ZAFIRA:
            return Response({"message": "Invalid app source"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserCreateSerializerInput(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                user = serializer.save()
        except Exception as e:
            return save_error_api(request, e)

        # return Response(user.to_json_api(), status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_201_CREATED)
