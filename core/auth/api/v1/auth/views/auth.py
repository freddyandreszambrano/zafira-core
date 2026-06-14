from django.db import transaction
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny

from core.auth.api.v1.auth.features.auth_zafira import AuthApiZafira
from core.auth.api.v1.auth.serializer.user import AuthTokenSerializerInput
from core.common.error import save_error_api


class CustomAuthTokenApiView(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = AuthTokenSerializerInput(data=self.request.data)
                if serializer.is_valid(raise_exception=True):
                    username = serializer.validated_data['username']
                    if self.request.headers.get('app-source') == 'zafira-app':
                        auth_zafira = AuthApiZafira(self.request)
                        auth_zafira.login(username)

        except Exception as e:
            return save_error_api(self.request, e)

        response = super().post(self.request, *args, **kwargs)
        return response
