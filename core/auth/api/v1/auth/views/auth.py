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
from core.profiles.models import MobileProfile


class CustomAuthTokenApiView(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        auth = AuthApiZafira(self.request)
        try:
            with transaction.atomic():
                serializer = AuthTokenSerializerInput(data=self.request.data)
                serializer.is_valid(raise_exception=True)

                username = serializer.validated_data["username"]
                password = serializer.validated_data["password"]

                if auth.check_disabled_account(username, password):
                    return Response(
                        {
                            "message": (
                                "Tu cuenta ha sido desactivada. "
                                "Contacta al soporte para más información."
                            )
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

                if not auth.is_valid_source():
                    return Response(
                        {"message": "Invalid app source"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                auth.login(username)
        except Exception as e:
            return save_error_api(self.request, e)

        return auth.build_response(super().post(self.request, *args, **kwargs))


class CurrentUserApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(
            {"user": request.user.to_json_api()},
            status=status.HTTP_200_OK,
        )


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

        return Response(
            {
                "message": "Perfil actualizado correctamente",
                "user": user.to_json_api(),
            },
            status=status.HTTP_200_OK,
        )


class UserAvatarUpdateApiView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        image = request.FILES.get("image")

        if not image:
            return Response(
                {"message": "Debe adjuntar una imagen."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        user.image = image
        user.save(update_fields=["image"])

        return Response(
            {
                "message": "Foto de perfil actualizada correctamente",
                "user": user.to_json_api(),
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, *args, **kwargs):
        user = request.user

        if user.image:
            user.image.delete(save=False)
            user.image = None
            user.save(update_fields=["image"])

        return Response(
            {
                "message": "Foto de perfil eliminada correctamente",
                "user": user.to_json_api(),
            },
            status=status.HTTP_200_OK,
        )


class TryOnPhotoUpdateApiView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        image = request.FILES.get("image")

        if not image:
            return Response(
                {"message": "Debe adjuntar una imagen."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        mobile_profile, _ = MobileProfile.objects.get_or_create(user=request.user)
        mobile_profile.try_on_photo = image
        mobile_profile.save(update_fields=["try_on_photo"])

        return Response(
            {
                "message": "Foto guardada correctamente",
                "user": request.user.to_json_api(),
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, *args, **kwargs):
        mobile_profile = getattr(request.user, "mobile_profile", None)

        if mobile_profile and mobile_profile.try_on_photo:
            mobile_profile.try_on_photo.delete(save=False)
            mobile_profile.try_on_photo = None
            mobile_profile.save(update_fields=["try_on_photo"])

        return Response(
            {
                "message": "Foto eliminada correctamente",
                "user": request.user.to_json_api(),
            },
            status=status.HTTP_200_OK,
        )
