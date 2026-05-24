"""URL configuration for authentication module."""

from django.urls import path
from .views import (
    IndexRedirectView,
    LoginView, RegisterView, LogoutView, DashboardView, UsersListView,
    ListUsersAjaxView, EditUserAjaxView, DeleteUserAjaxView,
    ChangePasswordAjaxView, ResetPasswordAjaxView
)

root_urls = [
    path('', IndexRedirectView.as_view(), name='index'),
]

web_urls = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('users/', UsersListView.as_view(), name='users_list'),
]

ajax_urls = [
    path('api/users/list/', ListUsersAjaxView.as_view(), name='api-users-list'),
    path('api/users/edit/', EditUserAjaxView.as_view(), name='api-users-edit'),
    path('api/users/delete/', DeleteUserAjaxView.as_view(), name='api-users-delete'),
    path('api/users/change-password/', ChangePasswordAjaxView.as_view(), name='api-users-change-password'),
    path('api/users/reset-password/', ResetPasswordAjaxView.as_view(), name='api-users-reset-password'),
]

urlpatterns = root_urls + web_urls + ajax_urls
