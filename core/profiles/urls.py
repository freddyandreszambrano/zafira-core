from rest_framework.routers import SimpleRouter

from .views import UserProfileViewSet

router = SimpleRouter()
router.register(r"profiles", UserProfileViewSet, basename="profile")

urlpatterns = list(router.urls)
