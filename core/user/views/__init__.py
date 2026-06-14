from .dashboard import DashboardView
from .user import (
    PasswordChangeView,
    ProfileEditView,
    ProfileManageView,
    ProfileView,
    UserCreateView,
    UserDeleteView,
    UserListView,
    UserUpdateView,
)

__all__ = [
    "DashboardView",
    "ProfileView",
    "ProfileEditView",
    "ProfileManageView",
    "PasswordChangeView",
    "UserListView",
    "UserCreateView",
    "UserUpdateView",
    "UserDeleteView",
]
