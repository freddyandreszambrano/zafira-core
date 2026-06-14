from django.urls import path

from core.auth.api.v1.auth.views.auth import CustomAuthTokenApiView

urlpatterns = [
    path('-token', CustomAuthTokenApiView.as_view(), name='api_token_auth'),
]
