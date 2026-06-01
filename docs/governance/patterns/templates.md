# Templates

Cómo escribir templates en ZAFIRA-CORE.

## Estructura base

Cada CRUD tiene 3 templates dentro de la app:

```
core/catalog/templates/company/
├── list.html      # DataTable list
├── form.html      # Create + Update (mismo template)
└── delete.html    # Delete confirm
```

## List template

Hereda de `templates/list.html` (base global).

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

**Bloques disponibles:**
- `{% block columns %}` — columnas del DataTable
- `{% block head_list %}` — scripts/libs específicas

## Form template

Hereda de `templates/form.html` (base global). **Se usa para Create Y Update.**

```html
{# core/catalog/templates/company/form.html #}
{% extends 'form.html' %}
{% load static %}
{% load widget_tweaks %}

{% block head_form %}
    <script src="{% static 'company/js/form.js' %}"></script>
{% endblock %}
```

**El template base (`templates/form.html`) se encarga de:**
- Renderizar el form con CSRF token
- Mostrar errors
- Botones Submit/Cancel

**El contexto pasa:**
- `form` → el formulario
- `action` → `'add'` (Create) o `'edit'` (Update)
- `title` → título de la página

## Delete template

Hereda de `templates/delete.html` (base global).

```html
{# core/catalog/templates/company/delete.html #}
{% extends 'delete.html' %}
```

**Mínimo.** El base maneja todo (confirm + AJAX delete).

## Los templates base (globales)

Están en `templates/`:

### `base.html`
Layout principal: nav, sidebar dinámico, footer.

```html
{# templates/base.html #}
<!DOCTYPE html>
<html>
<head>
    <title>ZAFIRA</title>
    {% block head %}{% endblock %}
</head>
<body>
    {% include 'partials/nav.html' %}
    
    <div class="container-fluid">
        <div class="row">
            {% include 'partials/sidebar.html' %}
            
            <main class="col-md-9">
                {% if messages %}
                    {% for message in messages %}
                        <div class="alert alert-{{ message.tags }}">
                            {{ message }}
                        </div>
                    {% endfor %}
                {% endif %}
                
                {% block content %}{% endblock %}
            </main>
        </div>
    </div>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

### `base_public.html`
Layout sin sidebar (login/register).

```html
{# templates/base_public.html #}
<!DOCTYPE html>
<html>
<head>
    <title>ZAFIRA - Login</title>
    {% block head %}{% endblock %}
</head>
<body class="login-page">
    <div class="login-container">
        {% block content %}{% endblock %}
    </div>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

### `list.html`
Base para listas con DataTable.

```html
{# templates/list.html #}
{% extends 'base.html' %}
{% load static %}

{% block content %}
<div class="card">
    <div class="card-header">
        <h4>{{ title }}</h4>
        <a href="{{ create_url }}" class="btn btn-primary float-right">
            <i class="fas fa-plus"></i> Crear
        </a>
    </div>
    
    <div class="card-body">
        <table id="data" class="table table-striped table-bordered">
            <thead>
                <tr>
                    {% block columns %}{% endblock %}
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>
</div>

{% block head_list %}{% endblock %}
{% endblock %}
```

Pasa `title` y `create_url` desde la vista.

### `form.html`
Base para crear/editar.

```html
{# templates/form.html #}
{% extends 'base.html' %}
{% load widget_tweaks %}

{% block content %}
<div class="card">
    <div class="card-header">
        <h4>{{ title }}</h4>
    </div>
    
    <div class="card-body">
        <form id="frmForm" method="post">
            {% csrf_token %}
            
            {% for field in form %}
                <div class="form-group">
                    <label for="{{ field.id_for_label }}">{{ field.label }}</label>
                    {% render_form field %}
                    
                    {% if field.errors %}
                        <div class="invalid-feedback d-block">
                            {{ field.errors }}
                        </div>
                    {% endif %}
                </div>
            {% endfor %}
            
            <div class="form-group">
                <input type="hidden" name="action" value="{{ action }}">
                <button type="submit" class="btn btn-primary">
                    {% if action == 'add' %}Crear{% else %}Guardar{% endif %}
                </button>
                <a href="{{ list_url }}" class="btn btn-secondary">Cancelar</a>
            </div>
        </form>
    </div>
</div>

{% block head_form %}{% endblock %}
{% endblock %}
```

Pasa `action` ('add' o 'edit'), `title`, `list_url` desde la vista.

### `delete.html`
Base para confirmar delete.

```html
{# templates/delete.html #}
{% extends 'base.html' %}

{% block content %}
<div class="card card-danger">
    <div class="card-header">
        <h4>{{ title }}</h4>
    </div>
    
    <div class="card-body">
        <p>¿Está seguro que desea eliminar este registro?</p>
        <p class="text-danger"><strong>Esta acción no se puede deshacer.</strong></p>
    </div>
    
    <div class="card-footer">
        <form method="post" style="display: inline">
            {% csrf_token %}
            <button type="submit" class="btn btn-danger">Eliminar</button>
            <a href="{{ list_url }}" class="btn btn-secondary">Cancelar</a>
        </form>
    </div>
</div>

{% block head_delete %}{% endblock %}
{% endblock %}
```

Pasa `title`, `list_url` desde la vista.

## Cómo pasar contexto desde la vista

En `get_context_data()`:

```python
# core/catalog/views/company.py
class CompanyListView(PermissionMixin, TemplateView):
    template_name = 'company/list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Empresas'
        context['create_url'] = reverse_lazy('company_create')
        return context
```

## Buen ejemplo: lista completa

```html
{# core/catalog/templates/company/list.html #}
{% extends 'list.html' %}
{% load static %}

{% comment %} 
Tabla de empresas con búsqueda, paginación y toggle de estado.
Ver core/catalog/static/company/js/list.js para la lógica.
{% endcomment %}

{% block columns %}
    <th>Nombre</th>
    <th class="text-center">Activo</th>
    <th class="text-center">Acciones</th>
{% endblock %}

{% block head_list %}
    <script src="{% static 'company/js/list.js' %}"></script>
{% endblock %}
```

## Buen ejemplo: form completo

```html
{# core/catalog/templates/company/form.html #}
{% extends 'form.html' %}
{% load static %}
{% load widget_tweaks %}

{% comment %} 
Formulario de crear/editar empresa. 
Validación en vivo con FormValidation + remote.
Ver core/catalog/static/company/js/form.js para la lógica.
{% endcomment %}

{% block head_form %}
    <script src="{% static 'company/js/form.js' %}"></script>
{% endblock %}
```

## Cosas que NO hacer

### ❌ No metas JS inline

**Malo:**
```html
{% block head_list %}
    <script>
        let table = Zafira.dataTable(...)
    </script>
{% endblock %}
```

**Bueno:**
```html
{% block head_list %}
    <script src="{% static 'company/js/list.js' %}"></script>
{% endblock %}
```

### ❌ No hagas templates pass-through vacíos

**Malo:**
```html
{# core/catalog/templates/company/form.html #}
{% extends 'form.html' %}
{# nada más #}
```

**Si no hay nada específico:**
```python
# En la vista:
template_name = 'form.html'  # apunta directo al base
```

### ❌ No dupliques el base.html

Siempre hereda de `base.html` (directo o vía otros bases como `list.html`).

### ❌ No hardcodees URLs

**Malo:**
```html
<a href="/company/">Atrás</a>
```

**Bueno:**
```html
<a href="{% url 'company_list' %}">Atrás</a>
```

## Helpers útiles

### `{% static %}`
Carga archivos estáticos.

```html
<script src="{% static 'company/js/list.js' %}"></script>
<link rel="stylesheet" href="{% static 'css/custom.css' %}">
```

### `{% url %}`
Genera URLs por nombre.

```html
<a href="{% url 'company_list' %}">Lista</a>
<a href="{% url 'company_create' %}">Crear</a>
<a href="{% url 'company_update' object.id %}">Editar</a>
<a href="{% url 'company_delete' object.id %}">Borrar</a>
```

### `{% csrf_token %}`
Token CSRF en forms.

```html
<form method="post">
    {% csrf_token %}
    ...
</form>
```

### `{% load widget_tweaks %}`
Renderiza fields con atributos.

```html
{% load widget_tweaks %}
{{ form.name|add_class:"form-control" }}
{{ form.is_active|add_class:"form-check-input" }}
```

### Renderizar form completo
```html
{% for field in form %}
    <div class="form-group">
        <label>{{ field.label }}</label>
        {{ field }}
        {% if field.errors %}
            <div class="error">{{ field.errors }}</div>
        {% endif %}
    </div>
{% endfor %}
```

---

**TL;DR:** 3 templates por CRUD (list/form/delete), hereda de globales, JS externo siempre.
