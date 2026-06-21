from django.urls import path

from core.auth.api.v1.auth.views.auth import (
    CustomAuthTokenApiView,
    MobileProfileUpdateApiView,
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
        "profile/update/",
        MobileProfileUpdateApiView.as_view(),
        name="api_v1_auth_profile_update",
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
