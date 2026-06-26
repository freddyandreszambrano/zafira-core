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
from core.profiles.models import MobileProfile


def _serialize_user(request, user):
    mobile_profile = getattr(user, "mobile_profile", None)

    image_url = ""
    if getattr(user, "image", None):
        image_url = request.build_absolute_uri(user.image.url)

    try_on_photo_url = ""
    if getattr(mobile_profile, "try_on_photo", None):
        try_on_photo_url = request.build_absolute_uri(mobile_profile.try_on_photo.url)

    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "dni": getattr(user, "dni", ""),
        "image": image_url,
        "gender": getattr(mobile_profile, "gender", ""),
        "country": getattr(mobile_profile, "country", ""),
        "preferred_size": getattr(mobile_profile, "preferred_size", ""),
        "style_preferences": getattr(mobile_profile, "style_preferences", {}),
        "language": getattr(mobile_profile, "language", "es"),
        "try_on_photo": try_on_photo_url,
    }


class CustomAuthTokenApiView(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = AuthTokenSerializerInput(data=self.request.data)
                serializer.is_valid(raise_exception=True)

                username = serializer.validated_data["username"]
                password = serializer.validated_data["password"]
                app_source = self.request.headers.get("app-source")

                User = get_user_model()
                existing_user = User.objects.filter(username=username).first()
                if (
                    existing_user is not None
                    and not existing_user.is_active
                    and existing_user.check_password(password)
                ):
                    return Response(
                        {"message": "Tu cuenta ha sido desactivada. Contacta al soporte para más información."},
                        status=status.HTTP_403_FORBIDDEN,
                    )

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
            response.data["user"] = _serialize_user(self.request, user)

        return response


class CurrentUserApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(
            {"user": _serialize_user(request, request.user)},
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
                "user": _serialize_user(request, user),
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
                "user": _serialize_user(request, user),
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
                "user": _serialize_user(request, user),
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
                "user": _serialize_user(request, request.user),
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
                "user": _serialize_user(request, request.user),
            },
            status=status.HTTP_200_OK,
        )
