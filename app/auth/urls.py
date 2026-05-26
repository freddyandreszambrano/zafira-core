from django.urls import path

from .views import (
    DashboardView,
    IndexRedirectView,
    LoginView,
    LogoutView,
    PasswordChangeView,
    ProfileEditView,
    ProfileView,
    RegisterView,
    UserCreateView,
    UserDeleteView,
    UserListView,
    UserUpdateView,
)


root_urls = [
    path('', IndexRedirectView.as_view(), name='index'),
]

public_urls = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
]

session_urls = [
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]

users_urls = [
    path('user/', UserListView.as_view(), name='user_list'),
    path('user/create/', UserCreateView.as_view(), name='user_create'),
    path('user/update/<int:pk>/', UserUpdateView.as_view(), name='user_update'),
    path('user/delete/<int:pk>/', UserDeleteView.as_view(), name='user_delete'),
]

profile_urls = [
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
    path('profile/password/', PasswordChangeView.as_view(), name='password_change'),
]

urlpatterns = root_urls + public_urls + session_urls + users_urls + profile_urls
