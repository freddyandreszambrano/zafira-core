from django.urls import path

from core.auth.api.v1.auth.views.auth import (
    CurrentUserApiView,
    CustomAuthTokenApiView,
    MobileProfileUpdateApiView,
    TryOnPhotoUpdateApiView,
    UserAvatarUpdateApiView,
)
from core.auth.api.v1.auth.views.password_reset import (
    PasswordResetConfirmApiView,
    PasswordResetRequestApiView,
)

urlpatterns = [
    path(
        "token/",
        CustomAuthTokenApiView.as_view(),
        name="api_v1_auth_token",
    ),
    path(
        "profile/me/",
        CurrentUserApiView.as_view(),
        name="api_v1_auth_current_user",
    ),
    path(
        "profile/update/",
        MobileProfileUpdateApiView.as_view(),
        name="api_v1_auth_profile_update",
    ),
    path(
        "profile/avatar/",
        UserAvatarUpdateApiView.as_view(),
        name="api_v1_auth_profile_avatar",
    ),
    path(
        "profile/try-on-photo/",
        TryOnPhotoUpdateApiView.as_view(),
        name="api_v1_auth_profile_try_on_photo",
    ),
    path(
        "password-reset/request/",
        PasswordResetRequestApiView.as_view(),
        name="api_v1_password_reset_request",
    ),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmApiView.as_view(),
        name="api_v1_password_reset_confirm",
    ),
]
