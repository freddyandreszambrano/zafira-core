# Patrón CRUD

Cómo implementar un CRUD completo en ZAFIRA-CORE.

**TL;DR:** 4 views explícitas (`List/Create/Update/Delete`) + templates en la app + JS externo.

## 1. Modelo

```python
# core/catalog/models/company.py
from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.name

    def to_json(self):
        """REQUERIDO: para que el list AJAX serialice"""
        return {
            'id': self.id,
            'name': self.name,
            'is_active': self.is_active,
        }
```

**Reglas:**
- ✅ Incluye `to_json()` — lo usa el list para AJAX
- ✅ `__str__()` para representación en admin
- ✅ Claves únicas (name, email, etc.) con `unique=True`
- ✅ Booleano `is_active` para toggle de estado
- ❌ No uses `verbose_name` con acentos — Django + permisos raramente lo necesitan
- ❌ No metas docstrings obvios

## 2. Form

```python
# core/catalog/forms/company.py
from django import forms
from core.catalog.models import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'is_active']
```

**Reglas:**
- ✅ Hereda de `ModelForm` (automáticamente valida el modelo)
- ✅ Define qué campos se editan
- ❌ No agregues validadores aquí — la validación en vivo va en JS

## 3. Views

Cada CRUD tiene **4 views explícitas**. Cada `post()` maneja sus acciones con `if/elif`.

### 3.1 List View

```python
# core/catalog/views/company.py
import json
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from core.catalog.models import Company
from core.security.mixins import PermissionMixin

class CompanyListView(PermissionMixin, TemplateView):
    template_name = 'company/list.html'
    permission_required = 'view_company'

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST.get('action', None)
        try:
            if action == 'search':
                # DataTables AJAX
                page = request.POST.get('page')
                page_size = request.POST.get('page_size')
                search_value = request.POST.get('search[value]', '')
                
                query = Q()
                if search_value:
                    query.add(Q(name__icontains=search_value), Q.OR)
                
                queryset = Company.objects.filter(query).order_by('-id')
                paginator = Paginator(queryset, page_size)
                paginated = paginator.get_page(page)
                
                data = {
                    'data': [item.to_json() for item in paginated],
                    'recordsTotal': paginator.count,
                    'recordsFiltered': paginator.count,
                }
                
            elif action == 'change_state':
                # Toggle is_active
                company = Company.objects.get(pk=request.POST.get('id'))
                company.is_active = not company.is_active
                company.save()
                
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
                
        except Exception as e:
            data['error'] = str(e)
        
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Empresas'
        context['create_url'] = reverse_lazy('company_create')
        return context
```

**Reglas:**
- ✅ Hereda de `PermissionMixin` y `TemplateView`
- ✅ `permission_required = 'view_company'`
- ✅ `post()` maneja AJAX con `if action == ...`
- ✅ Usa `to_json()` del modelo
- ✅ Usa `Q()` para búsquedas flexibles
- ❌ No deserialices Formsets — solo es JSON simple

### 3.2 Create View

```python
# core/catalog/views/company.py
class CompanyCreateView(PermissionMixin, CreateView):
    model = Company
    template_name = 'company/form.html'  # mismo que Update
    form_class = CompanyForm
    success_url = reverse_lazy('company_list')
    permission_required = 'add_company'

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
                # Validación en vivo
                pattern = request.POST.get('pattern', '')
                if pattern == 'name':
                    value = request.POST.get('name', '')
                    data['valid'] = not Company.objects.filter(name__iexact=value).exists()
                else:
                    data['valid'] = True
                    
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
                
        except Exception as e:
            data['error'] = str(e)
        
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear empresa'
        context['list_url'] = self.success_url
        context['action'] = 'add'  # para que el JS sepa que es create
        return context
```

**Reglas:**
- ✅ `action = 'add'` para guardar
- ✅ `action = 'validate_data'` para validación en vivo
- ✅ En `get_context_data()`, setea `context['action'] = 'add'` para que el JS sepa
- ✅ El mismo `template_name` que `UpdateView`

### 3.3 Update View

```python
# core/catalog/views/company.py
class CompanyUpdateView(PermissionMixin, UpdateView):
    model = Company
    template_name = 'company/form.html'  # mismo que Create
    form_class = CompanyForm
    success_url = reverse_lazy('company_list')
    permission_required = 'change_company'

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
                # Validación en vivo: EXCLUYE el objeto actual
                pattern = request.POST.get('pattern', '')
                if pattern == 'name':
                    value = request.POST.get('name', '')
                    data['valid'] = not Company.objects.filter(
                        name__iexact=value
                    ).exclude(pk=self.object.pk).exists()
                else:
                    data['valid'] = True
                    
            else:
                data['error'] = 'No ha seleccionado ninguna opción'
                
        except Exception as e:
            data['error'] = str(e)
        
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar empresa'
        context['list_url'] = self.success_url
        context['action'] = 'edit'  # para que el JS sepa que es update
        return context
```

**Reglas:**
- ✅ `action = 'edit'` para guardar (distinto de `'add'`)
- ✅ En `validate_data`, usa `.exclude(pk=self.object.pk)` para permitir el nombre actual
- ✅ Mismo `template_name` que `CreateView`
- ✅ En `get_context_data()`, setea `context['action'] = 'edit'`

### 3.4 Delete View

```python
# core/catalog/views/company.py
from django.views.generic import DeleteView

class CompanyDeleteView(PermissionMixin, DeleteView):
    model = Company
    template_name = 'company/delete.html'
    success_url = reverse_lazy('company_list')
    permission_required = 'delete_company'

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            self.get_object().delete()
            data['success'] = True
        except Exception as e:
            data['error'] = str(e)
        
        return HttpResponse(json.dumps(data), content_type='application/json')
```

**Reglas:**
- ✅ Simple y directa
- ✅ POST borra el objeto
- ❌ No uses `get_success_url()` complicado — redirección en JS

## 4. Re-exportar en `__init__.py`

```python
# core/catalog/views/__init__.py
from .company import (
    CompanyListView,
    CompanyCreateView,
    CompanyUpdateView,
    CompanyDeleteView,
)

__all__ = [
    'CompanyListView',
    'CompanyCreateView',
    'CompanyUpdateView',
    'CompanyDeleteView',
]
```

## 5. URLs

```python
# core/catalog/urls.py
from django.urls import path
from core.catalog.views import (
    CompanyListView,
    CompanyCreateView,
    CompanyUpdateView,
    CompanyDeleteView,
)

urlpatterns = [
    path('company/', CompanyListView.as_view(), name='company_list'),
    path('company/create/', CompanyCreateView.as_view(), name='company_create'),
    path('company/update/<int:pk>/', CompanyUpdateView.as_view(), name='company_update'),
    path('company/delete/<int:pk>/', CompanyDeleteView.as_view(), name='company_delete'),
]
```

Y en `config/urls.py`:
```python
urlpatterns = [
    # ...
    path('catalog/', include('core.catalog.urls')),
]
```

## 6. Templates

Ver [**patterns/templates.md**](templates.md) para detalles. Resumen:

```html
<!-- core/catalog/templates/company/list.html -->
{% extends 'list.html' %}
{% load static %}

{% block columns %}
    <th>Nombre</th>
    <th class="text-center">Activo</th>
    <th class="text-center">Acciones</th>
{% endblock %}

{% block head_list %}
    <script src="{% static 'company/js/list.js' %}"></script>
{% endblock %}
```

```html
<!-- core/catalog/templates/company/form.html -->
{% extends 'form.html' %}
{% load static %}

{% block head_form %}
    <script src="{% static 'company/js/form.js' %}"></script>
{% endblock %}
```

```html
<!-- core/catalog/templates/company/delete.html -->
{% extends 'delete.html' %}
```

## 7. JavaScript

Ver [**patterns/js.md**](js.md) para detalles. Resumen:

```javascript
// core/catalog/static/company/js/list.js
let tblCompany;

const company = {
    list: function() {
        tblCompany = Zafira.dataTable('#data', [
            { data: 'name' },
            { data: 'is_active', className: 'text-center', render: data => Zafira.statusBadge(data) },
            { data: 'id', className: 'text-center', orderable: false, render: id => Zafira.rowActions(id) },
        ], { toggleConfirm: '¿Cambiar el estado de esta empresa?' });
    }
};

$(function() { company.list(); });
```

```javascript
// core/catalog/static/company/js/form.js
let fv;

document.addEventListener('DOMContentLoaded', function() {
    fv = FormValidation.formValidation(document.getElementById('frmForm'), {
        locale: 'es_ES',
        localization: FormValidation.locales.es_ES,
        plugins: { /* ... */ },
        fields: {
            name: {
                validators: {
                    notEmpty: { message: 'Ingrese un nombre' },
                    stringLength: { min: 2 },
                    remote: {
                        url: pathname,
                        data: () => ({ name: fv.form.querySelector('[name="name"]').value, pattern: 'name', action: 'validate_data' }),
                        message: 'El nombre ya se encuentra registrado',
                        method: 'POST',
                        headers: { 'X-CSRFToken': csrftoken },
                    },
                },
            },
        },
    }).on('core.form.valid', function() {
        submit_formdata_with_ajax_form(fv);
    });
});
```

## 8. Registrar como Module

Edita `core/security/management/commands/insert_data.py`:

```python
{
    'type': 'Catálogos',
    'name': 'Empresas',
    'url': '/catalog/company/',
    'icon': 'fas fa-building',
    'description': 'Gestión de empresas',
    'permits_app': 'catalog',
    'permits_model': 'company',
    'order': 1,
},
```

## Checklist

- [ ] Modelo con `to_json()`
- [ ] Form con ModelForm
- [ ] 4 Views: List (search + change_state) | Create (add + validate) | Update (edit + validate) | Delete
- [ ] URLs en `urls.py` (list/create/update/delete)
- [ ] 3 Templates: list.html | form.html | delete.html
- [ ] 2 JS: list.js | form.js
- [ ] Re-exportar en `views/__init__.py`
- [ ] Registrar como Module en insert_data.py
- [ ] Corre `make migrate && make insert-data`
- [ ] Test: list, create, update, delete, validación en vivo

---

**Fuente de verdad:** `CLAUDE.md` en la raíz. Este documento lo amplía con ejemplos.
