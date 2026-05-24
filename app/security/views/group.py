from django.urls import reverse_lazy

from app.security.forms import GroupForm
from app.security.models import Group

from ._crud import CrudCreateView, CrudDeleteView, CrudListView, CrudUpdateView


class GroupListView(CrudListView):
    model = Group
    template_name = 'security/group/list.html'
    permission_required = 'view_group'
    list_title = 'Grupos'
    create_url_name = 'group_create'
    search_fields = ['name', 'description']
    toggle_field = 'is_active'


class GroupCreate(CrudCreateView):
    model = Group
    form_class = GroupForm
    template_name = 'security/group/form.html'
    permission_required = 'add_group'
    list_url_name = 'group_list'
    create_title = 'Crear grupo'
    unique_fields = ['name']
    success_url = reverse_lazy('group_list')


class GroupUpdate(CrudUpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'security/group/form.html'
    permission_required = 'change_group'
    list_url_name = 'group_list'
    update_title = 'Editar grupo'
    unique_fields = ['name']
    success_url = reverse_lazy('group_list')


class GroupDelete(CrudDeleteView):
    model = Group
    template_name = 'security/group/delete.html'
    permission_required = 'delete_group'
    list_url_name = 'group_list'
    success_url = reverse_lazy('group_list')
