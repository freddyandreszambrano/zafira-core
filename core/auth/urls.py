from django.urls import path, include

from .views import IndexRedirectView, LoginView, LogoutView, RegisterView

urlpatterns = [
    path("", IndexRedirectView.as_view(), name="index"),
    # Login
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # api_v1
    path("api_v1/", include("core.auth.api.v1.urls")),
]
