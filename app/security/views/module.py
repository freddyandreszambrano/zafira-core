from app.security.forms import ModuleForm, ModuleTypeForm
from app.security.models import Module, ModuleType

from ._crud import CrudCreateView, CrudDeleteView, CrudListView, CrudUpdateView


class ModuleTypeListView(CrudListView):
    model = ModuleType
    template_name = 'security/module_type/list.html'
    permission_required = 'view_moduletype'
    list_title = 'Tipos de módulo'
    create_url_name = 'module_type_create'
    search_fields = ['name', 'description']
    toggle_field = 'is_active'


class ModuleTypeCreate(CrudCreateView):
    model = ModuleType
    form_class = ModuleTypeForm
    template_name = 'security/module_type/form.html'
    permission_required = 'add_moduletype'
    list_url_name = 'module_type_list'
    create_title = 'Crear tipo de módulo'
    unique_fields = ['name']

    def get_success_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy('module_type_list')


class ModuleTypeUpdate(CrudUpdateView):
    model = ModuleType
    form_class = ModuleTypeForm
    template_name = 'security/module_type/form.html'
    permission_required = 'change_moduletype'
    list_url_name = 'module_type_list'
    update_title = 'Editar tipo de módulo'
    unique_fields = ['name']

    def get_success_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy('module_type_list')


class ModuleTypeDelete(CrudDeleteView):
    model = ModuleType
    template_name = 'security/module_type/delete.html'
    permission_required = 'delete_moduletype'
    list_url_name = 'module_type_list'

    def get_success_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy('module_type_list')


class ModuleListView(CrudListView):
    model = Module
    template_name = 'security/module/list.html'
    permission_required = 'view_module'
    list_title = 'Módulos'
    create_url_name = 'module_create'
    search_fields = ['name', 'url', 'description']
    toggle_field = 'is_active'


class ModuleCreate(CrudCreateView):
    model = Module
    form_class = ModuleForm
    template_name = 'security/module/form.html'
    permission_required = 'add_module'
    list_url_name = 'module_list'
    create_title = 'Crear módulo'
    unique_fields = ['url']

    def get_success_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy('module_list')


class ModuleUpdate(CrudUpdateView):
    model = Module
    form_class = ModuleForm
    template_name = 'security/module/form.html'
    permission_required = 'change_module'
    list_url_name = 'module_list'
    update_title = 'Editar módulo'
    unique_fields = ['url']

    def get_success_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy('module_list')


class ModuleDelete(CrudDeleteView):
    model = Module
    template_name = 'security/module/delete.html'
    permission_required = 'delete_module'
    list_url_name = 'module_list'

    def get_success_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy('module_list')
