from django.urls import path

from .views import (
    DashboardView,
    IndexRedirectView,
    LoginView,
    LogoutView,
    PasswordChangeView,
    ProfileEditView,
    ProfileManageView,
    ProfileView,
    RegisterView,
    UserCreateView,
    UserDeleteView,
    UserListView,
    UserUpdateView,
)

urlpatterns = [
    path('', IndexRedirectView.as_view(), name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('user/', UserListView.as_view(), name='user_list'),
    path('user/create/', UserCreateView.as_view(), name='user_create'),
    path('user/update/<int:pk>/', UserUpdateView.as_view(), name='user_update'),
    path('user/delete/<int:pk>/', UserDeleteView.as_view(), name='user_delete'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
    path('profile/manage/', ProfileManageView.as_view(), name='profile_manage'),
    path('profile/password/', PasswordChangeView.as_view(), name='password_change'),
]
