from django.urls import include, path

urlpatterns = [
    path("user/", include("core.user.api.v1.user.urls")),
]
