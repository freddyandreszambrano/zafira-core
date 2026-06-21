from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.auth.api.v1.auth.features.auth_zafira import AuthApiZafira
from core.auth.api.v1.auth.serializer.user import (
    AuthTokenSerializerInput,
    MobileProfileUpdateSerializer,
)
from core.common.error import save_error_api


class CustomAuthTokenApiView(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = AuthTokenSerializerInput(data=self.request.data)
                serializer.is_valid(raise_exception=True)

                username = serializer.validated_data["username"]
                app_source = self.request.headers.get("app-source")

                if app_source in AuthApiZafira.app_sources:
                    AuthApiZafira(self.request).login(username)
                else:
                    return Response(
                        {"message": "Invalid app source"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except Exception as e:
            return save_error_api(self.request, e)

        response = super().post(self.request, *args, **kwargs)

        User = get_user_model()
        user = User.objects.filter(username=username).first()

        if user is not None:
            mobile_profile = getattr(user, "mobile_profile", None)

            response.data["user"] = {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "dni": getattr(user, "dni", ""),
                "image": user.image.url if getattr(user, "image", None) else "",
                "gender": getattr(mobile_profile, "gender", ""),
                "country": getattr(mobile_profile, "country", ""),
                "preferred_size": getattr(
                    mobile_profile,
                    "preferred_size",
                    "",
                ),
                "style_preferences": getattr(
                    mobile_profile,
                    "style_preferences",
                    {},
                ),
            }

        return response


class MobileProfileUpdateApiView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        serializer = MobileProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        mobile_profile = getattr(user, "mobile_profile", None)

        return Response(
            {
                "message": "Perfil actualizado correctamente",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "dni": getattr(user, "dni", ""),
                    "image": user.image.url if getattr(user, "image", None) else "",
                    "gender": getattr(mobile_profile, "gender", ""),
                    "country": getattr(mobile_profile, "country", ""),
                    "preferred_size": getattr(
                        mobile_profile,
                        "preferred_size",
                        "",
                    ),
                    "style_preferences": getattr(
                        mobile_profile,
                        "style_preferences",
                        {},
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )
