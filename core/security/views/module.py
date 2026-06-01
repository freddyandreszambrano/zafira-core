import json

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from core.security.forms import ModuleForm, ModuleTypeForm
from core.security.mixins import PermissionMixin
from core.security.models import Module, ModuleType


class ModuleTypeListView(PermissionMixin, TemplateView):
    template_name = 'module_type/list.html'
    permission_required = 'view_moduletype'

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST.get('action', None)
        try:
            if action == 'search':
                data = []
                page = request.POST.get('page')
                page_size = request.POST.get('page_size')
                search_value = request.POST.get('search[value]', '')
                query = Q()
                if search_value:
                    query.add((Q(name__icontains=search_value) |
                               Q(description__icontains=search_value)), Q.OR)
                queryset = ModuleType.objects.filter(query).order_by('-id')
                paginator = Paginator(queryset, page_size)
                paginated_data = paginator.get_page(page)
                response = [item.to_json() for item in paginated_data]
                data = {'data': response, 'recordsTotal': paginator.count, 'recordsFiltered': paginator.count}
            elif action == 'change_state':
                module_type = ModuleType.objects.get(pk=request.POST.get('id'))
                module_type.is_active = not module_type.is_active
                module_type.save()
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Tipos de módulo'
        context['create_url'] = reverse_lazy('module_type_create')
        return context


class ModuleTypeCreateView(PermissionMixin, CreateView):
    model = ModuleType
    template_name = 'module_type/form.html'
    form_class = ModuleTypeForm
    success_url = reverse_lazy('module_type_list')
    permission_required = 'add_moduletype'

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST.get('action', None)
        try:
            if action == 'add':
                form = self.get_form()
                if form.is_valid():
                    form.save()
                    data['success'] = True
                else:
                    data['error'] = form.errors.as_json()
            elif action == 'validate_data':
                pattern = request.POST.get('pattern', '')
                if pattern == 'name':
                    value = request.POST.get('name', '')
                    data['valid'] = not ModuleType.objects.filter(name__iexact=value).exists()
                else:
                    data['valid'] = True
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear tipo de módulo'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        return context


class ModuleTypeUpdateView(PermissionMixin, UpdateView):
    model = ModuleType
    template_name = 'module_type/form.html'
    form_class = ModuleTypeForm
    success_url = reverse_lazy('module_type_list')
    permission_required = 'change_moduletype'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST.get('action', None)
        try:
            if action == 'edit':
                form = self.get_form()
                if form.is_valid():
                    form.save()
                    data['success'] = True
                else:
                    data['error'] = form.errors.as_json()
            elif action == 'validate_data':
                pattern = request.POST.get('pattern', '')
                if pattern == 'name':
                    value = request.POST.get('name', '')
                    data['valid'] = not ModuleType.objects.exclude(pk=self.object.pk).filter(name__iexact=value).exists()
                else:
                    data['valid'] = True
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar tipo de módulo'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        return context


class ModuleTypeDeleteView(PermissionMixin, DeleteView):
    model = ModuleType
    template_name = 'module_type/delete.html'
    success_url = reverse_lazy('module_type_list')
    permission_required = 'delete_moduletype'

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            self.get_object().delete()
            data['success'] = True
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_url'] = self.success_url
        return context


__all__ = [
    'ModuleTypeListView', 'ModuleTypeCreateView', 'ModuleTypeUpdateView', 'ModuleTypeDeleteView',
    'ModuleListView', 'ModuleCreateView', 'ModuleUpdateView', 'ModuleDeleteView',
]


class ModuleListView(PermissionMixin, TemplateView):
    template_name = 'module/list.html'
    permission_required = 'view_module'

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST.get('action', None)
        try:
            if action == 'search':
                data = []
                page = request.POST.get('page')
                page_size = request.POST.get('page_size')
                search_value = request.POST.get('search[value]', '')
                query = Q()
                if search_value:
                    query.add((Q(name__icontains=search_value) |
                               Q(url__icontains=search_value) |
                               Q(description__icontains=search_value)), Q.OR)
                queryset = Module.objects.filter(query).order_by('-id')
                paginator = Paginator(queryset, page_size)
                paginated_data = paginator.get_page(page)
                response = [item.to_json() for item in paginated_data]
                data = {'data': response, 'recordsTotal': paginator.count, 'recordsFiltered': paginator.count}
            elif action == 'change_state':
                module = Module.objects.get(pk=request.POST.get('id'))
                module.is_active = not module.is_active
                module.save()
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Módulos'
        context['create_url'] = reverse_lazy('module_create')
        return context


class ModuleCreateView(PermissionMixin, CreateView):
    model = Module
    template_name = 'module/form.html'
    form_class = ModuleForm
    success_url = reverse_lazy('module_list')
    permission_required = 'add_module'

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST.get('action', None)
        try:
            if action == 'add':
                form = self.get_form()
                if form.is_valid():
                    form.save()
                    data['success'] = True
                else:
                    data['error'] = form.errors.as_json()
            elif action == 'validate_data':
                pattern = request.POST.get('pattern', '')
                if pattern == 'url':
                    value = request.POST.get('url', '')
                    data['valid'] = not Module.objects.filter(url__iexact=value).exists()
                else:
                    data['valid'] = True
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear módulo'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        return context


class ModuleUpdateView(PermissionMixin, UpdateView):
    model = Module
    template_name = 'module/form.html'
    form_class = ModuleForm
    success_url = reverse_lazy('module_list')
    permission_required = 'change_module'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST.get('action', None)
        try:
            if action == 'edit':
                form = self.get_form()
                if form.is_valid():
                    form.save()
                    data['success'] = True
                else:
                    data['error'] = form.errors.as_json()
            elif action == 'validate_data':
                pattern = request.POST.get('pattern', '')
                if pattern == 'url':
                    value = request.POST.get('url', '')
                    data['valid'] = not Module.objects.exclude(pk=self.object.pk).filter(url__iexact=value).exists()
                else:
                    data['valid'] = True
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar módulo'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        return context


class ModuleDeleteView(PermissionMixin, DeleteView):
    model = Module
    template_name = 'module/delete.html'
    success_url = reverse_lazy('module_list')
    permission_required = 'delete_module'

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            self.get_object().delete()
            data['success'] = True
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_url'] = self.success_url
        return context
