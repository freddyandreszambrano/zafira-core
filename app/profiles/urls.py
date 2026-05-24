"""URL configuration for profiles module."""

from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import UserProfileViewSet, UserProfileDetailView

# Router for ViewSets
router = SimpleRouter()
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    # ViewSet routes (CRUD for profiles)
    *router.urls,

    # Custom endpoint for current user's profile
    path('profile/', UserProfileDetailView.as_view(), name='profile-detail'),
]
