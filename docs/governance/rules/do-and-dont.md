# Do's and Don'ts

Errores comunes y cómo evitarlos.

## ❌ ERRORES FRECUENTES

### 1. ❌ Crear clase base "CrudXxxView" para deduplicar

**Malo:**
```python
class CrudView(TemplateView):
    """Base CRUD"""
    def post(self, request, ...):
        action = request.POST.get('action')
        # toda la lógica acá
        ...

class CompanyListView(CrudView):
    ...
```

**Por qué es malo:**
- La abstracción oculta la lógica
- Difícil de debuggear
- Si una vista necesita ser diferente, rompe la jerarquía
- Linealidad es mejor que abstracción genérica

**Bueno:**
```python
class CompanyListView(PermissionMixin, TemplateView):
    def post(self, request, ...):
        action = request.POST.get('action', None)
        if action == 'search':
            ...
        elif action == 'change_state':
            ...

class ProductListView(PermissionMixin, TemplateView):
    def post(self, request, ...):
        action = request.POST.get('action', None)
        if action == 'search':  # puede ser diferente para cada entidad
            ...
        elif action == 'change_state':
            ...
```

✅ Repetición controlada y legible es preferible.

---

### 2. ❌ Poner JavaScript inline en templates

**Malo:**
```html
<!-- app/catalog/templates/company/list.html -->
{% extends 'list.html' %}

{% block head_list %}
    <script>
        let tblCompany;
        const company = { list: function() { ... } };
        $(function() { company.list(); });
    </script>
{% endblock %}
```

**Por qué es malo:**
- Difícil de testear
- Difícil de reutilizar
- Mezcla estructura (HTML) con comportamiento (JS)

**Bueno:**
```html
<!-- app/catalog/templates/company/list.html -->
{% extends 'list.html' %}
{% load static %}

{% block head_list %}
    <script src="{% static 'company/js/list.js' %}"></script>
{% endblock %}
```

```javascript
// app/catalog/static/company/js/list.js
let tblCompany;
const company = { list: function() { ... } };
$(function() { company.list(); });
```

✅ JS externo, limpio y separado.

---

### 3. ❌ Crear vistas AJAX separadas

**Malo:**
```python
# app/catalog/views.py
class CompanyListView(TemplateView):
    template_name = 'company/list.html'
    ...

class CompanyAjaxListView(TemplateView):  # ❌ Separada
    def post(self, request):
        action = request.POST.get('action')
        if action == 'search':
            ...

# urls.py
path('company/ajax/', CompanyAjaxListView.as_view(), name='company_ajax'),
```

**Por qué es malo:**
- Divide la lógica en dos vistas
- Confunde dónde ir a buscar el código
- Innecesariamente complejo

**Bueno:**
```python
# app/catalog/views.py
class CompanyListView(PermissionMixin, TemplateView):
    template_name = 'company/list.html'
    def post(self, request, ...):
        action = request.POST.get('action', None)
        if action == 'search':
            # AJAX aquí
            ...
        elif action == 'change_state':
            # AJAX aquí
            ...

# urls.py
path('company/', CompanyListView.as_view(), name='company_list'),
```

✅ Una vista, una URL, toda la lógica junto.

---

### 4. ❌ Hardcodear texto UI en español en el modelo

**Malo:**
```python
class Department(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Departamento"  # ❌ Texto quemado
    )
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
    ]
```

**Por qué es malo:**
- Difícil de cambiar UI sin tocar BD
- Mezcla datos con presentación
- `verbose_name` casi nunca se usa (Django admin es minoritario)

**Bueno:**
```python
# app/catalog/models/department.py
class Department(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

# app/common/constants.py
FORM_INPUT_CLASS = "w-full px-3 py-2 border border-gray-300 rounded"
MSG_DEPARTMENT_CREATED = "Departamento creado exitosamente"
MSG_DEPARTMENT_UPDATED = "Departamento actualizado"
MSG_DEPARTMENT_DELETED = "Departamento eliminado"

# En la vista:
messages.success(request, MSG_DEPARTMENT_CREATED)
```

✅ Texto de UI en constants, no en modelo.

---

### 5. ❌ Docstrings obvios

**Malo:**
```python
def get_active_companies():
    """Get all active companies."""
    return Company.objects.filter(is_active=True)

class CompanyListView(TemplateView):
    """List view for companies."""
    ...
```

**Por qué es malo:**
- El nombre ya dice qué hace
- Llena el código de ruido
- Docstring obvio = deuda técnica

**Bueno:**
```python
def get_active_companies():
    # Sin docstring si es obvio
    return Company.objects.filter(is_active=True)

class CompanyListView(PermissionMixin, TemplateView):
    # Sin docstring si es obvio
    ...
```

✅ Solo comenta el WHY no obvio (casos edge, hacks, invariantes).

---

### 6. ❌ No poner templates en `app/`

**Malo:**
```
templates/
├── company/
│   ├── list.html
│   ├── form.html
│   └── delete.html
```

**Por qué es malo:**
- La raíz `templates/` debe tener SOLO bases compartidos
- Hace difícil encontrar templates específicos
- Django puede conflictuar names

**Bueno:**
```
app/catalog/templates/
├── company/
│   ├── list.html
│   ├── form.html
│   └── delete.html
```

✅ Templates de entidad dentro de la app. Django las encuentra automáticamente.

---

### 7. ❌ Usar clases base que duplican lógica

**Malo:**
```python
class BaseListView(TemplateView):
    def get_queryset(self):
        # lógica compartida (pero casi nunca es igual para todas)
        return self.model.objects.all()

class CompanyListView(BaseListView):
    model = Company
```

**Bueno:**
```python
class CompanyListView(PermissionMixin, TemplateView):
    def get_queryset(self):
        # lógica específica
        return Company.objects.filter(is_active=True)
```

✅ Cero abstracción prematuro. Si 3 vistas comparten, *entonces* extraer.

---

### 8. ❌ Usar `dict(MODEL_CHOICES)` en views

**Malo:**
```python
# model
STATUS = [('active', 'Activo'), ('inactive', 'Inactivo')]

# view
from app.models import STATUS
status_dict = dict(STATUS)
return HttpResponse(json.dumps({'status': status_dict}))
```

**Bueno:**
```python
# model
STATUS = [('active', 'Activo'), ('inactive', 'Inactivo')]

# en el template o JS:
{% for value, label in form.status.field.choices %}
    {{ label }}
{% endfor %}

# en API:
from django.db.models import TextChoices
class Status(TextChoices):
    ACTIVE = 'active', 'Activo'
    INACTIVE = 'inactive', 'Inactivo'

# en la vista:
Status.choices  # retorna las tuplas
Status.ACTIVE.value  # 'active'
Status.ACTIVE.label  # 'Activo'
```

✅ Usa Django built-in choices, no dict manuales.

---

## ✅ BUENAS PRÁCTICAS

### 1. ✅ Modulariza agresivamente

Si un archivo pasa de ~200 líneas o tiene >5 clases → convierte en paquete:

**Antes:**
```
app/catalog/models.py      (300 líneas)
app/catalog/forms.py       (200 líneas)
app/catalog/views.py       (500 líneas)
```

**Después:**
```
app/catalog/models/__init__.py (re-exporta)
app/catalog/models/company.py
app/catalog/models/product.py

app/catalog/forms/__init__.py
app/catalog/forms/company.py
app/catalog/forms/product.py

app/catalog/views/__init__.py
app/catalog/views/company.py
app/catalog/views/product.py
```

✅ Cada archivo ~100-150 líneas, fácil de leer.

---

### 2. ✅ Imports al top del archivo

**Malo:**
```python
def get_companies():
    from app.catalog.models import Company  # ❌ Dentro de la función
    return Company.objects.all()
```

**Bueno:**
```python
from app.catalog.models import Company

def get_companies():
    return Company.objects.all()
```

✅ Todos los imports en el tope, excepto en casos muy especiales (circular imports).

---

### 3. ✅ Usa PermissionMixin en TODA vista CRUD

```python
from app.security.mixins import PermissionMixin

class CompanyListView(PermissionMixin, TemplateView):
    permission_required = 'view_company'
    ...
```

✅ Valida permisos automáticamente.

---

### 4. ✅ Todos los modelos deben tener `to_json()`

```python
class Company(models.Model):
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_active': self.is_active,
        }
```

✅ Usado por List view para AJAX responses.

---

### 5. ✅ Usa FormValidation + remote para validación en vivo

```javascript
// form.js
remote: {
    url: pathname,
    data: () => ({ 
        name: fv.form.querySelector('[name="name"]').value, 
        pattern: 'name', 
        action: 'validate_data' 
    }),
    message: 'El nombre ya se encuentra registrado',
    method: 'POST',
    headers: { 'X-CSRFToken': csrftoken },
},
```

✅ Validación sin refrescar, feedback inmediato.

---

### 6. ✅ Usa DataTables para listas

```javascript
// list.js
const company = {
    list: function() {
        tblCompany = Zafira.dataTable('#data', [
            { data: 'name' },
            { data: 'is_active', className: 'text-center', render: data => Zafira.statusBadge(data) },
            { data: 'id', className: 'text-center', orderable: false, render: id => Zafira.rowActions(id) },
        ], { toggleConfirm: '¿Cambiar estado?' });
    }
};

$(function() { company.list(); });
```

✅ DataTables maneja paginación, búsqueda, ordenamiento automáticamente.

---

### 7. ✅ Tests reales (no scaffolding vacío)

```python
# app/catalog/tests/test_company.py
from django.test import TestCase
from app.catalog.models import Company

class CompanyModelTest(TestCase):
    def test_str(self):
        c = Company.objects.create(name='Acme')
        self.assertEqual(str(c), 'Acme')
    
    def test_unique_name(self):
        Company.objects.create(name='Acme')
        with self.assertRaises(Exception):
            Company.objects.create(name='Acme')

    def test_to_json(self):
        c = Company.objects.create(name='Acme', is_active=True)
        json = c.to_json()
        self.assertEqual(json['name'], 'Acme')
        self.assertTrue(json['is_active'])
```

✅ Tests que verifican comportamiento real.

---

## Checklist rápido

- [ ] ¿Cada view es autocontenida? (sin clases base "CrudXxxView")
- [ ] ¿Templates están en `app/<app>/templates/<entity>/`?
- [ ] ¿JS está en archivos externos, no inline?
- [ ] ¿Uso PermissionMixin?
- [ ] ¿Tengo `to_json()` en los modelos?
- [ ] ¿Uso FormValidation + remote?
- [ ] ¿Sin docstrings obvios?
- [ ] ¿Modularizado en paquetes (<200 líneas)?
- [ ] ¿Imports al top?

---

Fuente: `CLAUDE.md` + experiencia del proyecto.
