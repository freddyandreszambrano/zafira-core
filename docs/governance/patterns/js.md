# JavaScript

Cómo escribir JS en ZAFIRA-CORE.

## Estructura

Cada CRUD tiene 2 archivos JS:

```
app/catalog/static/company/js/
├── list.js      # DataTable + columnas + acciones de lista
└── form.js      # FormValidation + validaciones específicas
```

## Patrón: objeto con métodos

```javascript
// app/catalog/static/company/js/list.js

const company = {
    list: function() {
        // DataTable setup
    },
    search: function() {
        // Search logic (si necesitas)
    },
    changeState: function(id) {
        // Toggle is_active
    }
};

$(function() {
    company.list();
});
```

**Por qué este patrón:**
- ✅ Namespace: evita conflictos globales
- ✅ Métodos organizados
- ✅ Fácil de debuggear
- ✅ Se lee linealmente

## list.js — DataTable

### Básico

```javascript
// app/catalog/static/company/js/list.js
let tblCompany;

const company = {
    list: function() {
        tblCompany = Zafira.dataTable('#data', [
            { data: 'name' },
            { 
                data: 'is_active', 
                className: 'text-center', 
                render: data => Zafira.statusBadge(data) 
            },
            { 
                data: 'id', 
                className: 'text-center', 
                orderable: false, 
                render: id => Zafira.rowActions(id) 
            },
        ], { 
            toggleConfirm: '¿Cambiar el estado de esta empresa?' 
        });
    }
};

$(function() { company.list(); });
```

**Qué hace `Zafira.dataTable()`:**
- Inicializa DataTable en `#data`
- Define columnas (mapeo a `to_json()` del modelo)
- AJAX automática a la vista (action=search)
- Paginación, búsqueda, ordenamiento automáticos
- Toggle (is_active) con confirmación

### Columnas comunes

```javascript
// Texto simple
{ data: 'name' }

// Con clase CSS
{ data: 'name', className: 'text-center' }

// Con render personalizado
{ 
    data: 'is_active', 
    render: function(data, type, row) {
        return Zafira.statusBadge(data);  // True → badge verde
    }
}

// Sin ordenamiento
{ data: 'id', orderable: false }

// Acciones (editar/borrar)
{
    data: 'id',
    className: 'text-center',
    orderable: false,
    render: id => Zafira.rowActions(id)  // enlaza a company_update/delete
}
```

### `Zafira.statusBadge(data)`

Renderiza booleano como badge:
```javascript
Zafira.statusBadge(true)   // → badge verde "Activo"
Zafira.statusBadge(false)  // → badge gris "Inactivo"
```

Con toggle:
```javascript
tblCompany = Zafira.dataTable('#data', [...], {
    toggleConfirm: '¿Cambiar estado?'  // ← toggle con confirm
});
```

Al clickear el badge:
- Manda POST a la misma URL con `action=change_state`
- La vista setea `is_active = not is_active`
- DataTable se recarga automáticamente

### `Zafira.rowActions(id)`

Renderiza botones Editar/Borrar:
```javascript
Zafira.rowActions(id)
```

Espera que las URLs estén nombradas:
- `{entity}_update` → botón Editar
- `{entity}_delete` → botón Borrar

Con confirmación de delete automática.

## form.js — FormValidation

### Básico

```javascript
// app/catalog/static/company/js/form.js
let fv;

document.addEventListener('DOMContentLoaded', function() {
    fv = FormValidation.formValidation(document.getElementById('frmForm'), {
        locale: 'es_ES',
        localization: FormValidation.locales.es_ES,
        plugins: {
            trigger: new FormValidation.plugins.Trigger(),
            submitButton: new FormValidation.plugins.SubmitButton(),
            bootstrap: new FormValidation.plugins.Bootstrap(),
            icon: new FormValidation.plugins.Icon({
                valid: 'fa fa-check',
                invalid: 'fa fa-times',
                validating: 'fa fa-refresh'
            }),
        },
        fields: {
            name: {
                validators: {
                    notEmpty: { message: 'Ingrese un nombre' },
                    stringLength: { min: 2, max: 120 },
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
                }
            },
            is_active: {
                validators: {
                    // Opcional: validadores específicos
                }
            }
        },
    }).on('core.form.valid', function() {
        submit_formdata_with_ajax_form(fv);
    });
});
```

**Qué hace:**
- Valida campos (notEmpty, stringLength, etc)
- Remote: valida en servidor (pattern=name → action=validate_data)
- Al submit: manda `action=add` (Create) o `action=edit` (Update)
- Helper `submit_formdata_with_ajax_form(fv)` maneja el AJAX

### Validadores comunes

```javascript
fields: {
    name: {
        validators: {
            notEmpty: { 
                message: 'Campo requerido' 
            },
            stringLength: { 
                min: 2, 
                max: 120,
                message: 'Entre 2 y 120 caracteres'
            },
            regexp: {
                regexp: /^[a-zA-Z0-9 ]+$/,
                message: 'Solo letras, números y espacios'
            },
            remote: { /* ... */ }
        }
    }
}
```

### Validación remote (en servidor)

```javascript
remote: {
    url: pathname,  // URL actual del form
    data: () => ({
        name: fv.form.querySelector('[name="name"]').value,
        pattern: 'name',  // qué campo estoy validando
        action: 'validate_data'  // qué acción
    }),
    message: 'El nombre ya se encuentra registrado',
    method: 'POST',
    headers: { 'X-CSRFToken': csrftoken },
},
```

En la vista:
```python
elif action == 'validate_data':
    pattern = request.POST.get('pattern', '')
    if pattern == 'name':
        value = request.POST.get('name', '')
        data['valid'] = not Company.objects.filter(name__iexact=value).exists()
```

**En Update, la vista automáticamente excluye el objeto actual:**
```python
.exclude(pk=self.object.pk)
```

Así el usuario puede dejar el mismo nombre.

### Múltiples validadores

```javascript
fields: {
    username: {
        validators: {
            notEmpty: { message: 'Requerido' },
            stringLength: { min: 3, max: 50 },
            remote: {
                url: pathname,
                data: () => ({ username: ..., pattern: 'username', action: 'validate_data' }),
                message: 'Ya existe',
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken },
            }
        }
    },
    email: {
        validators: {
            notEmpty: { message: 'Requerido' },
            emailAddress: { message: 'Email inválido' },
            remote: {
                url: pathname,
                data: () => ({ email: ..., pattern: 'email', action: 'validate_data' }),
                message: 'Email ya registrado',
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken },
            }
        }
    }
}
```

## Globals

Estos están disponibles en toda página (cargados en `base.html`):

```javascript
// Zafira.dataTable(selector, columns, options)
tblCompany = Zafira.dataTable('#data', [...])

// Zafira.statusBadge(boolean)
Zafira.statusBadge(true)  // → badge verde

// Zafira.rowActions(id)
Zafira.rowActions(123)  // → botones editar/borrar

// submit_formdata_with_ajax_form(fv)
submit_formdata_with_ajax_form(fv)  // maneja POST + redirect

// Variables globales
pathname          // URL actual (/catalog/company/)
csrftoken         // Token CSRF (del template)
```

## Ejemplo completo: User (más complejo)

```javascript
// app/auth/static/user/js/form.js
let fv;

document.addEventListener('DOMContentLoaded', function() {
    fv = FormValidation.formValidation(document.getElementById('frmForm'), {
        locale: 'es_ES',
        localization: FormValidation.locales.es_ES,
        plugins: {
            trigger: new FormValidation.plugins.Trigger(),
            submitButton: new FormValidation.plugins.SubmitButton(),
            bootstrap: new FormValidation.plugins.Bootstrap(),
            icon: new FormValidation.plugins.Icon({
                valid: 'fa fa-check',
                invalid: 'fa fa-times',
                validating: 'fa fa-refresh'
            }),
        },
        fields: {
            username: {
                validators: {
                    notEmpty: { message: 'Requerido' },
                    stringLength: { min: 3, max: 50 },
                    remote: {
                        url: pathname,
                        data: () => ({
                            username: fv.form.querySelector('[name="username"]').value,
                            pattern: 'username',
                            action: 'validate_data'
                        }),
                        message: 'Ya existe',
                        method: 'POST',
                        headers: { 'X-CSRFToken': csrftoken },
                    }
                }
            },
            email: {
                validators: {
                    notEmpty: { message: 'Requerido' },
                    emailAddress: { message: 'Email inválido' },
                    remote: {
                        url: pathname,
                        data: () => ({
                            email: fv.form.querySelector('[name="email"]').value,
                            pattern: 'email',
                            action: 'validate_data'
                        }),
                        message: 'Email ya registrado',
                        method: 'POST',
                        headers: { 'X-CSRFToken': csrftoken },
                    }
                }
            },
            password: {
                validators: {
                    notEmpty: { message: 'Requerido' },
                    stringLength: { min: 8, message: 'Mínimo 8 caracteres' }
                }
            }
        },
    }).on('core.form.valid', function() {
        submit_formdata_with_ajax_form(fv);
    });
});
```

## No hacer

### ❌ No uses `$.ajax()` directo

**Malo:**
```javascript
$('#btnSubmit').click(function() {
    $.ajax({
        url: pathname,
        data: formData,
        success: function(response) { ... }
    });
});
```

**Bueno:**
```javascript
fv.on('core.form.valid', function() {
    submit_formdata_with_ajax_form(fv);  // helper se encarga
});
```

### ❌ No hardcodees URLs

**Malo:**
```javascript
url: '/catalog/company/'
```

**Bueno:**
```javascript
url: pathname  // variable global = URL actual
```

### ❌ No confundas DataTable y FormValidation

- **DataTable** = para listas (list.js)
- **FormValidation** = para forms (form.js)

Cada uno en su archivo.

---

**TL;DR:** Patrón objeto + métodos, DataTable para listas, FormValidation para forms, helpers globales para AJAX.
