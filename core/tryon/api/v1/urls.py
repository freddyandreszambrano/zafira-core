from django.urls import include, path

urlpatterns = [
    path("tryon/", include("core.tryon.api.v1.tryon.urls")),
]
