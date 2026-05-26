from .auth import IndexRedirectView, LoginView, LogoutView, RegisterView
from .dashboard import DashboardView
from .users import UserCreateView, UserDeleteView, UserListView, UserUpdateView
from .profile import (
    PasswordChangeView,
    ProfileEditView,
    ProfileManageView,
    ProfileUpdateAPIView,
    ProfileView,
)

__all__ = [
    'IndexRedirectView',
    'LoginView', 'RegisterView', 'LogoutView',
    'DashboardView',
    'UserListView', 'UserCreateView', 'UserUpdateView', 'UserDeleteView',
    'ProfileView', 'ProfileEditView', 'ProfileManageView',
    'PasswordChangeView', 'ProfileUpdateAPIView',
]
