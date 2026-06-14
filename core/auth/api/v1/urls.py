from django.urls import include, path

urlpatterns = [
    path("auth/", include("core.auth.api.v1.auth.urls")),
]
