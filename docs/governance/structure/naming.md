# Convenciones de Naming

Cómo nombrar archivos, variables, funciones, clases, etc.

## Python

### Modelos
- **Clase**: PascalCase singular → `Company`, `Product`, `UserProfile`
- **Archivo**: snake_case → `core/catalog/models/company.py`, `core/catalog/models/product.py`

```python
# core/catalog/models/company.py
class Company(models.Model):
    name = models.CharField(max_length=120)
```

### Forms
- **Clase**: `<Model>Form` → `CompanyForm`, `ProductForm`, `UserForm`
- **Archivo**: snake_case → `core/catalog/forms/company.py`

```python
# core/catalog/forms/company.py
class CompanyForm(forms.ModelForm):
    ...
```

### Views
- **Clase**: `<Model><Action>View` → `CompanyListView`, `CompanyCreateView`, `CompanyUpdateView`, `CompanyDeleteView`
- **Archivo**: snake_case → `core/catalog/views/company.py`

```python
# core/catalog/views/company.py
class CompanyListView(PermissionMixin, TemplateView):
    ...

class CompanyCreateView(PermissionMixin, CreateView):
    ...

class CompanyUpdateView(PermissionMixin, UpdateView):
    ...

class CompanyDeleteView(PermissionMixin, DeleteView):
    ...
```

### Variables y funciones
- **snake_case** → `company_name`, `get_active_users()`, `total_sales`

```python
def get_active_companies():
    return Company.objects.filter(is_active=True)

company_name = "Acme Corp"
total_sales = 1000.00
```

### Constantes
- **UPPER_SNAKE_CASE** → `MAX_USERS`, `FORM_INPUT_CLASS`, `MSG_SUCCESS`

```python
# core/common/constants.py
FORM_INPUT_CLASS = "w-full px-3 py-2 border border-gray-300 rounded"
MSG_SUCCESS = "Operación realizada exitosamente"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
```

## JavaScript

### Archivos
- **snake_case**: `list.js`, `form.js`, `helpers.js`

### Variables y funciones
- **camelCase**: `userData`, `getCompanyById()`, `validateEmail()`

```javascript
let userData = {};
const MAX_RETRIES = 3;

function getCompanyById(id) {
    return fetch(`/api/company/${id}`).then(r => r.json());
}
```

### Objetos y módulos
- **camelCase**: `company = { list: function() { } }`, `zafira = { dataTable: ... }`

```javascript
const company = {
    list: function() { /* ... */ },
    create: function() { /* ... */ },
    update: function() { /* ... */ },
    delete: function() { /* ... */ }
};
```

## Templates

### Directorios
- **snake_case**: `core/catalog/templates/company/`, `core/catalog/templates/product/`

### Archivos
- **snake_case**: `list.html`, `form.html`, `delete.html`, `_partial.html` (para includes)

```html
<!-- core/catalog/templates/company/list.html -->
<!-- core/catalog/templates/company/_status_badge.html (partial) -->
```

## URLs y paths

### URL patterns
- **snake_case con underscores para rutas**: `/company/`, `/user/create/`, `/product/update/123/`

```python
# core/catalog/urls.py
urlpatterns = [
    path('company/', CompanyListView.as_view(), name='company_list'),
    path('company/create/', CompanyCreateView.as_view(), name='company_create'),
    path('company/update/<int:pk>/', CompanyUpdateView.as_view(), name='company_update'),
    path('company/delete/<int:pk>/', CompanyDeleteView.as_view(), name='company_delete'),
]
```

### URL names
- **snake_case singular o plural según contexto**:
  - List: `company_list`, `companies` (menos común)
  - Create: `company_create`
  - Update: `company_update`, `company_edit` (menos común)
  - Delete: `company_delete`

## HTML IDs y clases

### IDs
- **snake_case, específicos y descriptivos**: `#data` (para DataTable), `#frmForm` (para Forms), `#btnSearch`

```html
<table id="data"></table>
<form id="frmForm"></form>
<button id="btnSearch">Buscar</button>
```

### CSS clases
- **Tailwind utility classes**: `w-full`, `px-3`, `py-2`, `border`, `rounded`
- **Custom classes si es necesario**: snake_case → `.company-card`, `.status-active`

```html
<div class="w-full px-3 py-2 border border-gray-300 rounded">
    <!-- content -->
</div>

<div class="company-card status-active">
    <!-- content -->
</div>
```

## Convenciones especiales

### Métodos de modelo
- `to_json()` — serialización para AJAX responses
- `__str__()` — representación en texto
- `get_absolute_url()` — URL canónica (si aplica)

```python
class Company(models.Model):
    name = models.CharField(max_length=120)
    
    def __str__(self):
        return self.name
    
    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_active': self.is_active,
        }
```

### Actions en POST
- **Convencionales para cada view**:
  - List: `search`, `change_state`
  - Create: `add`, `validate_data`
  - Update: `edit`, `validate_data`
  - Delete: (sin action, POST directo)

```python
# En la view
action = request.POST.get('action', None)
if action == 'search':
    ...
elif action == 'change_state':
    ...
elif action == 'add':  # o 'edit' en Update
    ...
elif action == 'validate_data':
    ...
```

### Permissions
- **Format**: `<action>_<model>` (Django default)
  - `view_company`
  - `add_company`
  - `change_company`
  - `delete_company`

```python
class CompanyListView(PermissionMixin, TemplateView):
    permission_required = 'view_company'
```

## Resumen rápido

| Cosa | Formato | Ejemplo |
|------|---------|---------|
| Modelo Python | PascalCase | `Company` |
| Archivo modelo | snake_case | `company.py` |
| Clase form | `<Model>Form` | `CompanyForm` |
| Clase view | `<Model><Action>View` | `CompanyListView` |
| Variable Python | snake_case | `company_name` |
| Constante Python | UPPER_SNAKE_CASE | `MSG_SUCCESS` |
| Variable JS | camelCase | `companyName` |
| Archivo JS | snake_case | `list.js` |
| Objeto JS | camelCase | `company = { ... }` |
| Directorio template | snake_case | `company/` |
| Archivo template | snake_case | `list.html` |
| URL path | snake_case | `/company/create/` |
| URL name | snake_case | `company_create` |
| HTML ID | snake_case | `#data`, `#frmForm` |
| HTML clase | Tailwind + custom snake_case | `w-full`, `.company-card` |

---

Consejo: **La consistencia importa más que la regla específica.** Si el proyecto ya usa `user_id` en todas partes, sigue eso aunque sea inconsistente con el resto.
