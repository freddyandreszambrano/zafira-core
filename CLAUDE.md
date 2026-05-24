# ZAFIRA-CORE — Guía para Claude

Este archivo es la gobernanza del proyecto para cualquier sesión de Claude. Léelo entero antes de hacer cambios.

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
app/
├── common/            # Compartido entre apps (NO depende de ninguna otra app)
│   ├── choices.py     # TextChoicesCustom + enums de dominio (Department, etc.)
│   ├── constants.py   # FORM_INPUT_CLASS, mensajes MSG_*
│   ├── mixins.py      # PublicMixin (reusable, no requiere security)
│   └── forms/widgets.py  # Factories: text_input(), password_input(), etc.
│
├── security/          # Sistema de Módulos y permisos dinámicos
│   ├── models/        # Module, ModuleType, Group, GroupModule, GroupPermission
│   ├── mixins.py      # PermissionMixin (USAR EN TODA VIEW CRUD), ModuleMixin
│   ├── views/_crud.py # CrudListView/CreateView/UpdateView/DeleteView (HEREDAR)
│   ├── views/{module,group}.py  # CRUD de las entidades de seguridad
│   ├── forms/         # ModuleForm, GroupForm, ModuleTypeForm
│   ├── context_processors.py  # `available_modules` para todos los templates
│   └── management/commands/insert_data.py  # Carga seed: módulos + admin/admin
│
├── auth/              # Autenticación (custom User model)
│   ├── models/        # User (con set_group_session/get_group_id_session)
│   ├── views/web.py   # Login/Register/Logout/Dashboard/Profile (NO usan PermissionMixin)
│   ├── views/users.py # User CRUD (USA CrudListView + permission_required)
│   ├── forms/         # auth.py, password.py, profile.py
│   └── serializers/   # API REST (DRF) si se necesita
│
└── profiles/          # UserProfile (datos extendidos del usuario)
    ├── models/        # UserProfile (usa Department de common.choices)
    └── views.py       # UserProfileViewSet (DRF API REST)

templates/
├── base.html          # Layout: nav con módulos dinámicos, CDNs, helpers JS
├── list.html          # Base DataTables (hijos definen {% block columns %} y {% block javascript_list %})
├── form.html          # Base form CRUD (renderiza todos los fields del form)
├── delete.html        # Base confirm + AJAX delete
├── security/{module,module_type,group}/list.html   # Solo lista, no form/delete (heredan del base)
├── users/list.html
└── shared/{auth,dashboard,profile}/   # Templates de auth (no CRUD)

core/
├── settings.py        # INSTALLED_APPS, MIDDLEWARE, context_processors
└── urls.py            # admin/, api/, security/, '' (auth)
```

**Regla**: si una entidad solo necesita el form/delete estándar, **NO crees** `form.html`/`delete.html` por entidad; la view apunta directo a `template_name = 'form.html'`. Solo crea hijos cuando necesites widgets/JS específicos.

---

## 3. Cómo agregar un nuevo módulo CRUD (paso a paso)

Supongamos que agregas `Company` en `app/catalog/`.

### Paso 1 — Modelo
```python
# app/catalog/models/company.py
from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self): return self.name

    def to_json(self):  # REQUERIDO para CrudListView (DataTables)
        return {'id': self.id, 'name': self.name, 'is_active': self.is_active}
```

### Paso 2 — Form
```python
# app/catalog/forms/company.py
from django import forms
from app.catalog.models import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'is_active']
```

### Paso 3 — Views (heredan del CRUD base)
```python
# app/catalog/views/company.py
from django.urls import reverse_lazy
from app.catalog.forms import CompanyForm
from app.catalog.models import Company
from app.security.views._crud import (
    CrudCreateView, CrudDeleteView, CrudListView, CrudUpdateView,
)

class CompanyListView(CrudListView):
    model = Company
    template_name = 'catalog/company/list.html'  # crea este (con columnas)
    permission_required = 'view_company'
    list_title = 'Empresas'
    create_url_name = 'company_create'
    search_fields = ['name']
    toggle_field = 'is_active'

class CompanyCreate(CrudCreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'form.html'                  # ← directo al base, no crees hijo
    permission_required = 'add_company'
    list_url_name = 'company_list'
    create_title = 'Crear empresa'
    unique_fields = ['name']
    success_url = reverse_lazy('company_list')

class CompanyUpdate(CrudUpdateView):
    # ... mismo patrón con permission_required='change_company', update_title='Editar empresa'

class CompanyDelete(CrudDeleteView):
    model = Company
    template_name = 'delete.html'                # ← directo al base
    permission_required = 'delete_company'
    list_url_name = 'company_list'
    success_url = reverse_lazy('company_list')
```

### Paso 4 — URLs
```python
# app/catalog/urls.py
from django.urls import path
from .views import CompanyCreate, CompanyDelete, CompanyListView, CompanyUpdate

urlpatterns = [
    path('company/', CompanyListView.as_view(), name='company_list'),
    path('company/create/', CompanyCreate.as_view(), name='company_create'),
    path('company/update/<int:pk>/', CompanyUpdate.as_view(), name='company_update'),
    path('company/delete/<int:pk>/', CompanyDelete.as_view(), name='company_delete'),
]
```
Y en `core/urls.py`: `path('catalog/', include('app.catalog.urls'))`.

### Paso 5 — Template de lista (solo columnas DataTables)
```html
{# templates/catalog/company/list.html #}
{% extends 'list.html' %}
{% block columns %}
    <th>Nombre</th>
    <th class="text-center">Activo</th>
    <th class="text-center">Acciones</th>
{% endblock %}
{% block javascript_list %}
<script>
  // Copiar el patrón de templates/security/module/list.html
</script>
{% endblock %}
```

### Paso 6 — Registrar como Module en el dashboard
Edita `app/security/management/commands/insert_data.py` y agrega:
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
- **Choices**: usar `TextChoicesCustom` de `app.common.choices` para enums, no listas de tuplas.
- **CSS form inputs**: usar `FORM_INPUT_CLASS` y los factories de `app.common.forms.widgets`, no duplicar la clase.

### Permisos
- **Toda view CRUD usa `PermissionMixin`** con `permission_required = 'view_xxx' / 'add_xxx' / 'change_xxx' / 'delete_xxx'`.
- Validación: `PermissionMixin` verifica contra `group.grouppermission_set` (no Django `user.has_perm`).
- Superuser: bypass automático en `PermissionMixin`.
- Vistas públicas (login/register): usar `PublicMixin` de `app.common.mixins`.

### Errores que NO cometer
- ❌ No crear vistas AJAX separadas (`xxxAjaxView`). Usar el patrón CRUD con `POST action='search'/'activate'/'add'/'edit'`.
- ❌ No usar `dict(MODEL_CHOICES)` en views. Usar `Choice.get_label(value)` o el built-in `obj.get_field_display()`.
- ❌ No agregar archivos vacíos solo "por consistencia". Si no aporta, no existe.
- ❌ No hardcodear texto del UI en español dentro del modelo (verbose_name OK, mensajes en `app.common.constants.MSG_*`).

### Tests
- Tests scaffolding listos en cada `app/*/tests/test_*.py`. Llenar con tests reales cuando agregues funcionalidad.
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

## 6. Sistema de Módulos — flujo completo

1. **Login** (`LoginView.post`) llama `user.set_group_session()` → mete el primer `security_group` activo del user en `request.session['group']`.
2. **Cada request** pasa por `crum.CurrentRequestUserMiddleware` → el request es accesible vía `get_current_request()` en cualquier punto.
3. **Cada render** ejecuta `app.security.context_processors.modules` → carga los `Module` del grupo en sesión, agrupados por `ModuleType`, y los inyecta como `available_modules` en TODOS los templates.
4. **`base.html`** itera `available_modules` para renderizar el dropdown del nav.
5. **`dashboard/home.html`** renderiza tarjetas agrupadas por `ModuleType`.
6. **Cada vista CRUD** decora `get()` con `@login_required` (vía PermissionMixin) y valida que el grupo activo tenga el `permission_required` declarado.

---

## 7. Pendientes conocidos / trampas

- **WSL + Windows Python + SQLite**: la BD se queda lockeada con frecuencia si tienes un IDE con `db.sqlite3` abierto. Usar `make kill-python` o cerrar el IDE.
- **`Token` viejos**: `signals.py` crea Token al guardar User. Si refactorizas auth, mantenlo o moverlo a `insert_data`.
- **Profile signals**: hay un signal en `profiles` que crea `UserProfile` automáticamente al crear User. No instanciar `UserProfile` directamente en views.
