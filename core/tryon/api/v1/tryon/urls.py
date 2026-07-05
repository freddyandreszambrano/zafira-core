from django.urls import path

from core.tryon.api.v1.tryon.views import TryOnCreateApiView, TryOnJobDetailApiView

urlpatterns = [
    path("", TryOnCreateApiView.as_view(), name="api_v1_tryon_create"),
    path("<uuid:job_id>/", TryOnJobDetailApiView.as_view(), name="api_v1_tryon_detail"),
]
