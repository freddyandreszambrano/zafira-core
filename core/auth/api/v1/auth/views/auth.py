from django.db import transaction

from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.auth.api.v1.auth.features.auth_zafira import AuthApiZafira
from core.auth.api.v1.auth.serializer.user import AuthTokenSerializerInput
from core.common.error import save_error_api


class CustomAuthTokenApiView(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        auth = AuthApiZafira(self.request)
        try:
            with transaction.atomic():
                serializer = AuthTokenSerializerInput(data=self.request.data)
                serializer.is_valid(raise_exception=True)

                if not auth.is_valid_source():
                    return Response(
                        {"message": "Invalid app source"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                auth.login(serializer.validated_data["username"])
        except Exception as e:
            return save_error_api(self.request, e)

        return auth.build_response(super().post(self.request, *args, **kwargs))
