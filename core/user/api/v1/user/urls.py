from django.urls import path

from core.user.api.v1.user.views.user import UserCreateApiView
from core.user.api.v1.user.views.validate_field import UserFieldValidationApiView

urlpatterns = [
    path(
        "create/",
        UserCreateApiView.as_view(),
        name="api_v1_user_create",
    ),
    path(
        "validate-field/",
        UserFieldValidationApiView.as_view(),
        name="api_v1_validate_field",
    ),
]
