import json

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from app.auth.forms import EditUserForm, RegisterForm
from app.auth.models import User
from app.security.mixins import PermissionMixin


class UserListView(PermissionMixin, TemplateView):
    template_name = 'user/list.html'
    permission_required = 'view_user'

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
                    query.add((Q(username__icontains=search_value) |
                               Q(email__icontains=search_value) |
                               Q(dni__icontains=search_value) |
                               Q(first_name__icontains=search_value) |
                               Q(last_name__icontains=search_value)), Q.OR)
                queryset = User.objects.filter(query).order_by('-id')
                paginator = Paginator(queryset, page_size)
                paginated_data = paginator.get_page(page)
                response = [item.to_json() for item in paginated_data]
                data = {'data': response, 'recordsTotal': paginator.count, 'recordsFiltered': paginator.count}
            elif action == 'change_state':
                user = User.objects.get(pk=request.POST.get('id'))
                user.is_active = not user.is_active
                user.save()
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Usuarios'
        context['create_url'] = reverse_lazy('user_create')
        return context


class UserCreateView(PermissionMixin, CreateView):
    model = User
    template_name = 'user/form.html'
    form_class = RegisterForm
    success_url = reverse_lazy('user_list')
    permission_required = 'add_user'

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
                if pattern in ('username', 'email', 'dni'):
                    value = request.POST.get(pattern, '')
                    data['valid'] = not User.objects.filter(**{f'{pattern}__iexact': value}).exists()
                else:
                    data['valid'] = True
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear usuario'
        context['list_url'] = self.success_url
        context['action'] = 'add'
        return context


class UserUpdateView(PermissionMixin, UpdateView):
    model = User
    template_name = 'user/form.html'
    form_class = EditUserForm
    success_url = reverse_lazy('user_list')
    permission_required = 'change_user'

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
                if pattern in ('username', 'email', 'dni'):
                    value = request.POST.get(pattern, '')
                    data['valid'] = not User.objects.exclude(pk=self.object.pk).filter(**{f'{pattern}__iexact': value}).exists()
                else:
                    data['valid'] = True
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
        except Exception as e:
            data['error'] = str(e)
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar usuario'
        context['list_url'] = self.success_url
        context['action'] = 'edit'
        return context


class UserDeleteView(PermissionMixin, DeleteView):
    model = User
    template_name = 'user/delete.html'
    success_url = reverse_lazy('user_list')
    permission_required = 'delete_user'

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


__all__ = ['UserListView', 'UserCreateView', 'UserUpdateView', 'UserDeleteView']
