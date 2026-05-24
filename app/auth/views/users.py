from django.urls import reverse_lazy

from app.auth.forms import EditUserForm, RegisterForm
from app.auth.models import User
from app.security.views._crud import (
    CrudCreateView,
    CrudDeleteView,
    CrudListView,
    CrudUpdateView,
)


def _user_to_json(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'dni': user.dni,
        'full_name': user.get_full_name(),
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'image': user.get_image_url(),
        'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M'),
    }


User.add_to_class('to_json', _user_to_json)


class UserListView(CrudListView):
    model = User
    template_name = 'users/list.html'
    permission_required = 'view_user'
    list_title = 'Usuarios'
    create_url_name = 'user_create'
    search_fields = ['username', 'email', 'dni', 'first_name', 'last_name']
    toggle_field = 'is_active'


class UserCreate(CrudCreateView):
    model = User
    form_class = RegisterForm
    template_name = 'users/form.html'
    permission_required = 'add_user'
    list_url_name = 'user_list'
    create_title = 'Crear usuario'
    unique_fields = ['username', 'email', 'dni']
    success_url = reverse_lazy('user_list')


class UserUpdate(CrudUpdateView):
    model = User
    form_class = EditUserForm
    template_name = 'users/form.html'
    permission_required = 'change_user'
    list_url_name = 'user_list'
    update_title = 'Editar usuario'
    unique_fields = ['username', 'email', 'dni']
    success_url = reverse_lazy('user_list')


class UserDelete(CrudDeleteView):
    model = User
    template_name = 'users/delete.html'
    permission_required = 'delete_user'
    list_url_name = 'user_list'
    success_url = reverse_lazy('user_list')
