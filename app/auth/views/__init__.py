from .auth import IndexRedirectView, LoginView, LogoutView, RegisterView
from .dashboard import DashboardView
from .users import UserCreate, UserDelete, UserListView, UserUpdate
from .web import (
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
    'UserListView', 'UserCreate', 'UserUpdate', 'UserDelete',
    'ProfileView', 'ProfileEditView', 'ProfileManageView',
    'PasswordChangeView', 'ProfileUpdateAPIView',
]
