from .auth import IndexRedirectView, LoginView, LogoutView, RegisterView
from .dashboard import DashboardView
from .profile import (
    PasswordChangeView,
    ProfileEditView,
    ProfileView,
)
from .users import UserCreateView, UserDeleteView, UserListView, UserUpdateView

__all__ = [
    'IndexRedirectView',
    'LoginView', 'RegisterView', 'LogoutView',
    'DashboardView',
    'UserListView', 'UserCreateView', 'UserUpdateView', 'UserDeleteView',
    'ProfileView', 'ProfileEditView',
    'PasswordChangeView',
]
