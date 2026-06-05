# ZAFIRA-CORE — Guía para agentes IA

Este archivo es la gobernanza del proyecto para cualquier sesión de agentes IA (Claude, Codex, Gemini, Cursor, Copilot). Léelo entero antes de hacer cambios.

> `AGENTS.md` y `CLAUDE.md` permanecen como symlinks en la raíz para auto-descubrimiento. Este archivo (`ai/AGENTS.md`) es la fuente de verdad.

> Para humanos: este es también un buen onboarding técnico.

---

## 1. Resumen del proyecto

**ZAFIRA-CORE** es un sistema administrativo Django con dashboard donde **cada módulo es configurable en base de datos**. La idea: agregar/quitar secciones del menú sin tocar código, solo desde la UI de administración de módulos.

**Stack:**
- Django 5.2 + DRF
- SQLite (dev) / PostgreSQL (prod)
- Tailwind CSS (CDN) + DataTables + FormValidation (frontend)
- `django-crum` (acceso al request actual desde modelos) + `django-widget-tweaks`

---

## 2. Estructura de carpetas

```
core/
├── common/            # Compartido entre apps (NO depende de ninguna otra app)
│   ├── choices.py     # TextChoicesCustom + enums de dominio (Department, etc.)
│   ├── constants.py   # FORM_INPUT_CLASS, mensajes MSG_*
│   ├── mixins.py      # PublicMixin (reusable, no requiere security)
│   └── forms/widgets.py  # Factories: text_input(), password_input(), etc.
│
├── security/          # Sistema de Módulos y permisos dinámicos
│   ├── models/        # Module, ModuleType, Group, GroupModule, GroupPermission
│   ├── mixins.py      # PermissionMixin (USAR EN TODA VIEW CRUD), ModuleMixin
│   ├── views/{module,group}.py  # CRUD explícito de las entidades de seguridad
│   ├── forms/         # ModuleForm, GroupForm, ModuleTypeForm
│   ├── templates/{module,module_type,group}/  # list.html + form.html + delete.html por entidad
│   ├── static/{module,module_type,group}/js/   # list.js + form.js por entidad
│   ├── context_processors.py  # `available_modules` para todos los templates
│   └── management/commands/insert_data.py  # Carga seed: módulos + admin/admin
│
├── auth/              # Autenticación (custom User model)
│   ├── models/        # User (con set_group_session/get_group_id_session, to_json)
│   ├── views/{auth,dashboard,profile}.py  # Login/Register/Logout/Dashboard/Profile (NO CRUD)
│   ├── views/users.py # User CRUD explícito (cada view define su post() inline)
│   ├── forms/         # auth.py, password.py, profile.py
│   ├── templates/{auth,dashboard,profile,user}/  # login, register, dashboard, profile, user CRUD
│   ├── static/user/js/  # list.js + form.js del User CRUD
│   └── serializers/   # API REST (DRF) si se necesita
│
└── profiles/          # UserProfile (datos extendidos del usuario)
    ├── models/        # UserProfile (usa Department de common.choices)
    └── views.py       # UserProfileViewSet (DRF API REST)

templates/             # SOLO bases compartidos entre apps
├── base.html          # Layout: nav con módulos dinámicos, CDNs, helpers JS
├── base_public.html   # Layout para login/register (sin sidebar)
├── list.html          # Base DataTables (hijos definen {% block columns %} y {% block head_list %})
├── form.html          # Base form CRUD ({% block head_form %} para libs/JS específicos)
└── delete.html        # Base confirm + AJAX delete ({% block head_delete %})

static/                # SOLO assets globales (CSS Tailwind compilado, etc.)
└── css/

config/
├── settings.py        # INSTALLED_APPS, MIDDLEWARE, context_processors
└── urls.py            # admin/, api/, security/, '' (auth)
```

**Reglas de ubicación**:
- **Templates y static específicos de una entidad viven dentro de la app**: `core/<app>/templates/<entity>/...` y `core/<app>/static/<entity>/...`. Django los encuentra automáticamente vía `APP_DIRS=True` y `staticfiles`.
- **`templates/` raíz solo contiene los bases verdaderamente compartidos** (`base.html`, `base_public.html`, `list.html`, `form.html`, `delete.html`). Nada de entidades específicas ahí.
- **Cada CRUD tiene 3 templates y 2 JS en su app**: `<entity>/list.html`, `<entity>/form.html`, `<entity>/delete.html` y `<entity>/js/list.js`, `<entity>/js/form.js`. El `form.html` lo comparten Create y Update (la diferencia la marca el contexto `action='add'|'edit'`). El `delete.html` suele ser solo `{% extends 'delete.html' %}` (la lógica AJAX vive en el base), pero existe para mantener el patrón uniforme y para poder agregar libs/JS específicos si hicieran falta.

---

## 3. Cómo agregar un nuevo módulo CRUD (paso a paso)

Patrón: **4 views explícitas y autocontenidas** — `XxxListView`, `XxxCreateView`, `XxxUpdateView`, `XxxDeleteView`. NO se hereda de "CrudXxx" base. Cada view define su `post()` inline con `if/elif action == ...` para que se lea de arriba a abajo.

Supongamos que agregas `Company` en `core/catalog/`.

### Paso 1 — Modelo
```python
# core/catalog/models/company.py
from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self): return self.name

    def to_json(self):  # REQUERIDO para que el list AJAX serialice
        return {'id': self.id, 'name': self.name, 'is_active': self.is_active}
```

### Paso 2 — Form
```python
# core/catalog/forms/company.py
from django import forms
from core.catalog.models import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'is_active']
```

### Paso 3 — Views (explícitas, autocontenidas)
Cada CRUD tiene 4 vistas. Cada `post()` maneja sus acciones con `if/elif`. Acciones convencionales:
- **List**: `'search'` (DataTables AJAX) y `'change_state'` (toggle del `is_active`).
- **Create**: `'add'` (guardar) y `'validate_data'` (unicidad en vivo).
- **Update**: `'edit'` y `'validate_data'`.
- **Delete**: sin `action`, POST directo.

```python
# core/catalog/views/company.py
import json

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from core.catalog.forms import CompanyForm
from core.catalog.models import Company
from core.security.mixins import PermissionMixin


class CompanyListView(PermissionMixin, TemplateView):
    template_name = 'catalog/company/list.html'
    permission_required = 'view_company'

    def post(self, request, *args, **kwargs):
        data = {}
        action = request.POST.get('action', None)
        try:
            if action == 'search':
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


class CompanyCreateView(PermissionMixin, CreateView):
    model = Company
    template_name = 'form.html'                  # ← directo al base, no crees hijo
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
        context['action'] = 'add'
        return context


class CompanyUpdateView(PermissionMixin, UpdateView):
    model = Company
    template_name = 'form.html'
    form_class = CompanyForm
    success_url = reverse_lazy('company_list')
    permission_required = 'change_company'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # mismo patrón que Create pero con action == 'edit' y filtro .exclude(pk=self.object.pk) en validate
        ...


class CompanyDeleteView(PermissionMixin, DeleteView):
    model = Company
    template_name = 'delete.html'                # ← directo al base
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

> Para ejemplos completos de `Update` (con `validate_data` y `exclude(pk=...)`) ver `core/security/views/module.py`.

### Paso 4 — URLs
```python
# core/catalog/urls.py
from django.urls import path
from .views import CompanyCreateView, CompanyDeleteView, CompanyListView, CompanyUpdateView

urlpatterns = [
    path('company/', CompanyListView.as_view(), name='company_list'),
    path('company/create/', CompanyCreateView.as_view(), name='company_create'),
    path('company/update/<int:pk>/', CompanyUpdateView.as_view(), name='company_update'),
    path('company/delete/<int:pk>/', CompanyDeleteView.as_view(), name='company_delete'),
]
```
Y en `config/urls.py`: `path('catalog/', include('core.catalog.urls'))`.

### Paso 5 — Templates + JS por entidad (app-local)

Cada CRUD tiene su propio set de 3 templates + 2 JS dentro de la app:

```
core/catalog/templates/company/
├── list.html      # extends 'list.html'
├── form.html      # extends 'form.html' (compartido por Create y Update)
└── delete.html    # extends 'delete.html'

core/catalog/static/company/js/
├── list.js        # DataTable + columnas
└── form.js        # FormValidation + validate_data remote
```

`APP_DIRS=True` (settings) + `staticfiles` hacen que Django los encuentre con paths sin prefijo (`'company/list.html'`, `'company/js/list.js'`).

Bloque expuesto por cada base para que el hijo cargue scripts/libs:
- `list.html` → `{% block head_list %}`
- `form.html` → `{% block head_form %}`
- `delete.html` → `{% block head_delete %}` (rara vez usado)

**Nunca poner JS inline en el template.**

```html
{# core/catalog/templates/company/list.html #}
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
{# core/catalog/templates/company/form.html — usado por Create Y Update #}
{% extends 'form.html' %}
{% load static %}
{% block head_form %}
    <script src="{% static 'company/js/form.js' %}"></script>
{% endblock %}
```

```html
{# core/catalog/templates/company/delete.html — passthrough, listo para futuras libs específicas #}
{% extends 'delete.html' %}
```

Y las views:
```python
class CompanyListView(PermissionMixin, TemplateView):
    template_name = 'company/list.html'

class CompanyCreateView(PermissionMixin, CreateView):
    template_name = 'company/form.html'      # mismo template que Update

class CompanyUpdateView(PermissionMixin, UpdateView):
    template_name = 'company/form.html'      # mismo template que Create

class CompanyDeleteView(PermissionMixin, DeleteView):
    template_name = 'company/delete.html'
```

```js
// core/catalog/static/company/js/list.js
let tblCompany;

const company = {
    list: function () {
        tblCompany = Zafira.dataTable('#data', [
            { data: 'name' },
            { data: 'is_active', className: 'text-center', render: data => Zafira.statusBadge(data) },
            { data: 'id', className: 'text-center', orderable: false, render: id => Zafira.rowActions(id) },
        ], { toggleConfirm: '¿Cambiar el estado de esta empresa?' });
    }
};

$(function () { company.list(); });
```

```js
// core/catalog/static/company/js/form.js — FormValidation con remote validate_data
let fv;

document.addEventListener('DOMContentLoaded', function () {
    fv = FormValidation.formValidation(document.getElementById('frmForm'), {
        locale: 'es_ES',
        localization: FormValidation.locales.es_ES,
        plugins: {
            trigger: new FormValidation.plugins.Trigger(),
            submitButton: new FormValidation.plugins.SubmitButton(),
            bootstrap: new FormValidation.plugins.Bootstrap(),
            icon: new FormValidation.plugins.Icon({ valid: 'fa fa-check', invalid: 'fa fa-times', validating: 'fa fa-refresh' }),
        },
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
    }).on('core.form.valid', function () {
        submit_formdata_with_ajax_form(fv);
    });
});
```

> El bloque `remote` envía `action='validate_data'` + `pattern=<campo>` a la vista; la vista responde `{valid: true|false}`. En Update la vista hace `.exclude(pk=self.object.pk)` automáticamente, por lo que el mismo `form.js` sirve para Create y Update.
> Si necesitas libs adicionales (select2, etc.) cárgalas dentro del mismo `{% block head_form %}` antes del `<script src="...form.js">`. Ver `core/auth/static/user/js/form.js` para un ejemplo con múltiples campos uniques (`username`, `email`, `dni`).

### Paso 6 — Registrar como Module en el dashboard
Edita `core/security/management/commands/insert_data.py` y agrega:
```python
{
    'type': 'Catálogos',  # crea ModuleType si no existe
    'name': 'Empresas',
    'url': '/catalog/company/',
    'icon': 'fas fa-building',
    'description': 'Gestión de empresas',
    'permits_app': 'catalog', 'permits_model': 'company',
    'order': 1,
},
```
Luego: `make migrate && make insert-data`. El módulo aparecerá en nav y dashboard automáticamente.

---

## 4. Reglas / convenciones

### Code style
- **Modularizar agresivamente**: si un archivo pasa de ~200 líneas o tiene >5 clases, dividirlo en paquete (`models/`, `views/`, `forms/`, etc.) con `__init__.py` que re-exporte.
- **Sin docstrings obvios**: NUNCA `"""Get user groups."""` en `get_groups()`. Solo escribe comentario si el WHY es no obvio.
- **Sin templates pass-through vacíos**: si solo dice `{% extends 'form.html' %}`, no lo crees — apunta `template_name` directo al base.
- **Imports al top del archivo** (no dentro de métodos).
- **Choices**: usar `TextChoicesCustom` de `core.common.choices` para enums, no listas de tuplas.
- **CSS form inputs**: usar `FORM_INPUT_CLASS` y los factories de `core.common.forms.widgets`, no duplicar la clase.

### Permisos
- **Toda view CRUD usa `PermissionMixin`** con `permission_required = 'view_xxx' / 'add_xxx' / 'change_xxx' / 'delete_xxx'`.
- Validación: `PermissionMixin` verifica contra `group.grouppermission_set` (no Django `user.has_perm`).
- Superuser: bypass automático en `PermissionMixin`.
- Vistas públicas (login/register): usar `PublicMixin` de `core.common.mixins`.

### Errores que NO cometer
- ❌ **No poner JS inline en templates de lista.** El JS de cada CRUD vive en `static/js/<app>/<entity>.js` con patrón objeto + método `list()` + `$(function(){ entity.list() })`. El template solo declara columnas y carga el script vía `{% static %}`.
- ❌ No crear vistas AJAX separadas (`xxxAjaxView`). Cada CRUD es 4 vistas (`List/Create/Update/Delete`) y cada una maneja sus acciones en `post()` con `if/elif action == 'search'/'change_state'/'add'/'edit'/'validate_data'`.
- ❌ No introducir mixins/clases base "CrudXxxView" para deduplicar el CRUD. La repetición controlada y leíble linealmente es preferible a la abstracción genérica.
- ❌ No usar `dict(MODEL_CHOICES)` en views. Usar `Choice.get_label(value)` o el built-in `obj.get_field_display()`.
- ❌ No agregar archivos vacíos solo "por consistencia". Si no aporta, no existe.
- ❌ No hardcodear texto del UI en español dentro del modelo (verbose_name OK, mensajes en `core.common.constants.MSG_*`).

### Tests
- Tests scaffolding listos en cada `core/*/tests/test_*.py`. Llenar con tests reales cuando agregues funcionalidad.
- `make test` corre todo. `make test-fast` reusa la BD.

---

## 5. Comandos `make` esenciales

| Comando | Para qué |
|---|---|
| `make setup` | Primera vez: install + migrate + insert-data. Usuario: `admin / admin` |
| `make run` | Levanta server en `0.0.0.0:8000` |
| `make migrate` / `make makemigrations` | Migraciones |
| `make insert-data` | Carga módulos + grupo Admin + usuario `admin/admin` |
| `make test` / `make test-fast` | Tests |
| `make kill-python` | Si la BD queda locked (común en WSL/Windows mixto) |
| `make reset-db` | ⚠ Borra `db.sqlite3` y recrea |

---

## 5.1. Estructura de raíz

La raíz se mantiene solo para puntos de entrada y archivos que herramientas esperan en esa ubicación (`README.md`, `AGENTS.md`, `CLAUDE.md`, `Makefile`, `manage.py`, `pyproject.toml`, `package.json`, `.env.example`, etc.).

Documentación secundaria y contexto de proyecto viven en `docs/`; ver `docs/project/root-files.md` para el mapa completo.

## 6. Sistema de Módulos — flujo completo

1. **Login** (`LoginView.post`) llama `user.set_group_session()` → mete el primer `security_group` activo del user en `request.session['group']`.
2. **Cada request** pasa por `crum.CurrentRequestUserMiddleware` → el request es accesible vía `get_current_request()` en cualquier punto.
3. **Cada render** ejecuta `core.security.context_processors.modules` → carga los `Module` del grupo en sesión, agrupados por `ModuleType`, y los inyecta como `available_modules` en TODOS los templates.
4. **`base.html`** itera `available_modules` para renderizar el dropdown del nav.
5. **`dashboard/home.html`** renderiza tarjetas agrupadas por `ModuleType`.
6. **Cada vista CRUD** decora `get()` con `@login_required` (vía PermissionMixin) y valida que el grupo activo tenga el `permission_required` declarado.

---

## 7. Pendientes conocidos / trampas

- **WSL + Windows Python + SQLite**: la BD se queda lockeada con frecuencia si tienes un IDE con `db.sqlite3` abierto. Usar `make kill-python` o cerrar el IDE.
- **`Token` viejos**: `signals.py` crea Token al guardar User. Si refactorizas auth, mantenlo o moverlo a `insert_data`.
- **Profile signals**: hay un signal en `profiles` que crea `UserProfile` automáticamente al crear User. No instanciar `UserProfile` directamente en views.
