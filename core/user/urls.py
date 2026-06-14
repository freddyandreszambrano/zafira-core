from django.urls import path, include

from views import DashboardView, UserListView, UserCreateView, UserUpdateView, UserDeleteView, ProfileView, \
    ProfileEditView, ProfileManageView, PasswordChangeView

urlpatterns = [
    # Dashboard
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    # User
    path("user/", UserListView.as_view(), name="user_list"),
    path("user/create/", UserCreateView.as_view(), name="user_create"),
    path("user/update/<int:pk>/", UserUpdateView.as_view(), name="user_update"),
    path("user/delete/<int:pk>/", UserDeleteView.as_view(), name="user_delete"),
    # Profile
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileEditView.as_view(), name="profile_edit"),
    path("profile/manage/", ProfileManageView.as_view(), name="profile_manage"),
    path("profile/password/", PasswordChangeView.as_view(), name="password_change"),
    # api_v1
    path('api_v1/', include('core.auth.api.v1.urls')),

]
