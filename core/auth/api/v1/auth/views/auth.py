from django.db import transaction

from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.auth.api.v1.auth.features import AuthApiZafira, MobileProfileApi
from core.auth.api.v1.auth.outputs import UserOutput
from core.auth.api.v1.auth.serializer.user import (
    AuthTokenSerializerInput,
    MobileProfileUpdateSerializer,
)
from core.common.error import save_error_api


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
            UserOutput(request.user).data,
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
        user = MobileProfileApi(request.user).update_profile(serializer.validated_data)

        return Response(
            UserOutput(user, "Perfil actualizado correctamente").data,
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

        user = MobileProfileApi(request.user).update_avatar(image)

        return Response(
            UserOutput(user, "Foto de perfil actualizada correctamente").data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, *args, **kwargs):
        user = MobileProfileApi(request.user).delete_avatar()

        return Response(
            UserOutput(user, "Foto de perfil eliminada correctamente").data,
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

        user = MobileProfileApi(request.user).update_try_on_photo(image)

        return Response(
            UserOutput(user, "Foto guardada correctamente").data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, *args, **kwargs):
        user = MobileProfileApi(request.user).delete_try_on_photo()

        return Response(
            UserOutput(user, "Foto eliminada correctamente").data,
            status=status.HTTP_200_OK,
        )
