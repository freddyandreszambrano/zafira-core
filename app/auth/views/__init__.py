from .users import UserCreate, UserDelete, UserListView, UserUpdate
from .web import (
    DashboardView,
    IndexRedirectView,
    LoginView,
    LogoutView,
    PasswordChangeView,
    ProfileEditView,
    ProfileManageView,
    ProfileUpdateAPIView,
    ProfileView,
    RegisterView,
)

__all__ = [
    'IndexRedirectView',
    'LoginView', 'RegisterView', 'LogoutView',
    'DashboardView',
    'UserListView', 'UserCreate', 'UserUpdate', 'UserDelete',
    'ProfileView', 'ProfileEditView', 'ProfileManageView',
    'PasswordChangeView', 'ProfileUpdateAPIView',
]
