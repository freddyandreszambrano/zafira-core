from django.urls import path

from core.user.api.v1.user.views.user import UserCreateApiView

urlpatterns = [
    path("create/", UserCreateApiView.as_view(), name="api_v1_user_create"),
]
