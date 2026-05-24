import json

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from app.security.mixins import PermissionMixin


def json_response(data):
    return HttpResponse(json.dumps(data, default=str), content_type='application/json')


class CrudListView(PermissionMixin, TemplateView):
    model = None
    search_fields: list[str] = []
    list_title = ''
    create_url_name: str | None = None
    page_size_default = 10
    toggle_field: str | None = None

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        try:
            if action == 'search':
                return json_response(self._search(request))
            if action == 'activate' and self.toggle_field:
                return json_response(self._toggle(request))
            return json_response({'error': 'Acción no soportada.'})
        except Exception as exc:
            return json_response({'error': str(exc)})

    def _search(self, request):
        page = request.POST.get('page', 1)
        page_size = int(request.POST.get('page_size', self.page_size_default))
        search_value = request.POST.get('search[value]', '')

        query = Q()
        if search_value and self.search_fields:
            for field in self.search_fields:
                query |= Q(**{f'{field}__icontains': search_value})

        queryset = self.model.objects.filter(query).order_by('-id')
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        return {
            'data': [item.to_json() for item in page_obj],
            'recordsTotal': paginator.count,
            'recordsFiltered': paginator.count,
        }

    def _toggle(self, request):
        obj = self.model.objects.get(pk=request.POST['id'])
        current = getattr(obj, self.toggle_field)
        setattr(obj, self.toggle_field, not current)
        obj.save(update_fields=[self.toggle_field])
        return {'success': True, 'state': not current}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.list_title
        if self.create_url_name:
            context['create_url'] = reverse_lazy(self.create_url_name)
        return context


class CrudCreateView(PermissionMixin, CreateView):
    model = None
    form_class = None
    list_url_name: str | None = None
    create_title = ''
    unique_fields: list[str] = []

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        try:
            if action == 'add':
                form = self.get_form()
                if form.is_valid():
                    form.save()
                    return json_response({'success': True})
                return json_response({'error': form.errors.as_json()})
            if action == 'validate_data':
                return json_response(self._validate(request))
            return json_response({'error': 'Acción no soportada.'})
        except Exception as exc:
            return json_response({'error': str(exc)})

    def _validate(self, request):
        pattern = request.POST.get('pattern', '')
        if pattern not in self.unique_fields:
            return {'valid': True}
        value = request.POST.get(pattern, '')
        exists = self.model.objects.filter(**{f'{pattern}__iexact': value}).exists()
        return {'valid': not exists}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.create_title
        if self.list_url_name:
            context['list_url'] = reverse_lazy(self.list_url_name)
        context['action'] = 'add'
        return context


class CrudUpdateView(PermissionMixin, UpdateView):
    model = None
    form_class = None
    list_url_name: str | None = None
    update_title = 'Editar'
    unique_fields: list[str] = []

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        try:
            if action == 'edit':
                form = self.get_form()
                if form.is_valid():
                    form.save()
                    return json_response({'success': True})
                return json_response({'error': form.errors.as_json()})
            if action == 'validate_data':
                return json_response(self._validate(request))
            return json_response({'error': 'Acción no soportada.'})
        except Exception as exc:
            return json_response({'error': str(exc)})

    def _validate(self, request):
        pattern = request.POST.get('pattern', '')
        if pattern not in self.unique_fields:
            return {'valid': True}
        value = request.POST.get(pattern, '')
        exists = (
            self.model.objects.exclude(pk=self.object.pk)
            .filter(**{f'{pattern}__iexact': value}).exists()
        )
        return {'valid': not exists}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.update_title
        if self.list_url_name:
            context['list_url'] = reverse_lazy(self.list_url_name)
        context['action'] = 'edit'
        return context


class CrudDeleteView(PermissionMixin, DeleteView):
    model = None
    list_url_name: str | None = None

    def post(self, request, *args, **kwargs):
        try:
            self.get_object().delete()
            return json_response({'success': True})
        except Exception as exc:
            return json_response({'error': str(exc)})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.list_url_name:
            context['list_url'] = reverse_lazy(self.list_url_name)
        return context
