# Estructura de Carpetas

Anatomía de ZAFIRA-CORE y dónde va cada cosa.

## Estructura general

```
ZAFIRA-CORE/
├── app/                      # Código fuente
│   ├── common/               # Compartido entre apps
│   ├── security/             # Módulos y permisos dinámicos
│   ├── auth/                 # Users, login, dashboard
│   ├── profiles/             # UserProfile
│   └── <new_app>/            # Tus nuevas apps van aquí
│
├── templates/                # SOLO bases compartidos
├── static/                   # SOLO assets globales
│
├── core/                     # Configuración Django (settings, urls)
├── manage.py                 # Django manage
├── Makefile                  # Comandos make
├── CLAUDE.md                 # ← GOBERNANZA DEL PROYECTO
│
├── docs/                     # Documentación
│   └── governance/           # ← Esta carpeta (para Claude)
│
└── db.sqlite3                # BD (dev, no commitear)
```

## Por app: estructura interna

Cada app sigue este patrón:

```
app/<app>/
├── __init__.py
├── models/
│   ├── __init__.py           # re-exporta: from .entity import Entity
│   ├── entity1.py            # from django.db import models
│   └── entity2.py
│
├── forms/
│   ├── __init__.py           # re-exporta: from .entity1 import Entity1Form
│   ├── entity1.py            # from django import forms
│   └── entity2.py
│
├── views/
│   ├── __init__.py           # re-exporta: from .entity1 import Entity1ListView, ...
│   ├── entity1.py            # List, Create, Update, Delete views
│   ├── entity2.py
│   └── dashboard.py          # vistas especiales (no CRUD)
│
├── serializers/              # (solo si hay REST API)
│   ├── __init__.py
│   └── entity1.py
│
├── templates/
│   ├── entity1/
│   │   ├── list.html         # {% extends 'list.html' %}
│   │   ├── form.html         # {% extends 'form.html' %} (crea Y edita)
│   │   └── delete.html       # {% extends 'delete.html' %}
│   │
│   └── entity2/
│       ├── list.html
│       ├── form.html
│       └── delete.html
│
├── static/
│   └── <entity>/js/
│       ├── list.js           # DataTable + columnas
│       └── form.js           # FormValidation + validaciones
│
├── migrations/               # Auto-generado por Django
│
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   └── test_forms.py
│
├── admin.py                  # Admin Django (si necesitas)
├── apps.py                   # Config de app
├── urls.py                   # URL patterns de esta app
├── management/               # (opcional) Django management commands
│   └── commands/
│       └── my_command.py
│
└── context_processors.py     # (opcional) Procesa contexto global
```

## Templates globales (raíz)

```
templates/
├── base.html                 # Layout principal: nav + sidebar + footer
├── base_public.html          # Layout sin sidebar (login/register)
├── list.html                 # Base para todo CRUD list (DataTable)
├── form.html                 # Base para Create + Update (form CRUD)
└── delete.html               # Base para Delete (confirm + AJAX)
```

**Regla:** Aquí SOLO van estos 5 templates. Cualquier template específico de entidad va dentro de la app.

## Static global (raíz)

```
static/
├── css/
│   ├── tailwind.css          # Compilado de Tailwind CDN
│   └── custom.css            # Overrides globales (si necesitas)
│
└── js/
    ├── zafira.js             # Helpers globales (Zafira.dataTable, Zafira.statusBadge, etc)
    └── utils.js              # Utilidades (formateo, validación, etc)
```

**Regla:** Aquí SOLO van assets realmente compartidos. JS específico de un CRUD va en su carpeta de app.

## Dónde va cada cosa

| Elemento | Dónde | Ejemplo |
|----------|-------|---------|
| Modelo de entidad | `app/<app>/models/<entity>.py` | `app/catalog/models/product.py` |
| Form de entidad | `app/<app>/forms/<entity>.py` | `app/catalog/forms/product.py` |
| Views de CRUD | `app/<app>/views/<entity>.py` | `app/catalog/views/product.py` |
| Template list | `app/<app>/templates/<entity>/list.html` | `app/catalog/templates/product/list.html` |
| Template form | `app/<app>/templates/<entity>/form.html` | `app/catalog/templates/product/form.html` |
| Template delete | `app/<app>/templates/<entity>/delete.html` | `app/catalog/templates/product/delete.html` |
| JS list | `app/<app>/static/<entity>/js/list.js` | `app/catalog/static/product/js/list.js` |
| JS form | `app/<app>/static/<entity>/js/form.js` | `app/catalog/static/product/js/form.js` |
| Serializer (DRF) | `app/<app>/serializers/<entity>.py` | `app/catalog/serializers/product.py` |
| Tests | `app/<app>/tests/test_<entity>.py` | `app/catalog/tests/test_product.py` |
| Choices / Enums | `app/common/choices.py` | `Department`, `Status`, etc. |
| Constants / MSG | `app/common/constants.py` | `FORM_INPUT_CLASS`, `MSG_SUCCESS`, etc. |
| Mixins reusables | `app/common/mixins.py` | `PublicMixin` (no requiere login) |
| Widgets de form | `app/common/forms/widgets.py` | `text_input()`, `password_input()`, etc. |

## Convención de imports

En `__init__.py` de paquetes, re-exporta lo importante:

```python
# app/catalog/models/__init__.py
from .company import Company
from .product import Product

__all__ = ['Company', 'Product']
```

Luego en views:
```python
from app.catalog.models import Company, Product  # ← Limpio
```

No:
```python
from app.catalog.models.company import Company  # ← Innecesariamente profundo
```

## Monolítico → Paquete

Si un archivo crece mucho, divídelo:

**Antes:** `app/catalog/views.py` (200+ líneas)

**Después:**
```
app/catalog/views/
├── __init__.py          # re-exporta
├── company.py           # CompanyListView, CompanyCreateView, ...
├── product.py           # ProductListView, ProductCreateView, ...
└── dashboard.py         # DashboardView, etc.
```

Re-exportar en `__init__.py`:
```python
from .company import CompanyListView, CompanyCreateView, CompanyUpdateView, CompanyDeleteView
from .product import ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView

__all__ = [
    'CompanyListView', 'CompanyCreateView', 'CompanyUpdateView', 'CompanyDeleteView',
    'ProductListView', 'ProductCreateView', 'ProductUpdateView', 'ProductDeleteView',
]
```

Y en `urls.py`:
```python
from app.catalog.views import CompanyListView, ProductListView
```

---

**TL;DR:** Templates y JS de entidad viven dentro de su app. Globales (base.html, list.html, form.html, delete.html) en `templates/` raíz.
