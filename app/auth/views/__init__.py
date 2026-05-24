from .views import (
    # Index/Root
    IndexRedirectView,
    # Web Views
    LoginView,
    RegisterView,
    LogoutView,
    DashboardView,
    UsersListView,
    # AJAX Views
    ListUsersAjaxView,
    EditUserAjaxView,
    DeleteUserAjaxView,
    ChangePasswordAjaxView,
    ResetPasswordAjaxView,
)

__all__ = [
    'IndexRedirectView',
    'LoginView',
    'RegisterView',
    'LogoutView',
    'DashboardView',
    'UsersListView',
    'ListUsersAjaxView',
    'EditUserAjaxView',
    'DeleteUserAjaxView',
    'ChangePasswordAjaxView',
    'ResetPasswordAjaxView',
]
