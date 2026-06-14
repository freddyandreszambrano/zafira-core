from django.urls import path

from core.profiles.views import MobileProfileDetailView, MobileProfileListView

urlpatterns = [
    path("mobile-profile/", MobileProfileListView.as_view(), name="mobile_profile_list"),
    path(
        "mobile-profile/detail/<int:pk>/",
        MobileProfileDetailView.as_view(),
        name="mobile_profile_detail",
    ),
]
