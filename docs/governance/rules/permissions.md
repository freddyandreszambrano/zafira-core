# Sistema de Permisos

Cómo funcionan los permisos en ZAFIRA-CORE.

## Conceptos

**Módulo** = una sección del dashboard + URL (ej: "Empresas" → `/catalog/company/`)
**Grupo** = conjunto de usuarios con permisos similares (ej: "Admin", "Supervisor")
**Permiso** = `view_<app>_<model>`, `add_<app>_<model>`, etc.

## Modelo de datos

```
Group
  ↓
GroupModule (un grupo tiene N módulos)
  ↓
GroupPermission (un grupo-módulo tiene permisos específicos)
```

Ejemplo:
- Grupo "Supervisor"
- Tiene módulo "Empresas"
- Con permisos: `view_company`, `change_company` (sin `add`, sin `delete`)

## Cómo funciona la validación

### En la vista

```python
class CompanyListView(PermissionMixin, TemplateView):
    permission_required = 'view_company'
    ...
```

**PermissionMixin** valida:
1. ¿Está logueado? → si no, redirige a login
2. ¿Es superuser? → sí → acesso permitido (bypass)
3. ¿Su grupo (en sesión) tiene el módulo? → ¿sí? → valida si tiene el permiso específico
4. ¿Tiene `view_company`? → sí → acceso permitido, no → 403 Forbidden

**No se usa Django `user.has_perm()`** — es específico de ZAFIRA-CORE.

### En la sesión

Al login:
```python
# auth/views/auth.py
def LoginView.post():
    user.set_group_session(request)  # ← setea request.session['group']
```

Esto mete el **primer grupo activo** del usuario en la sesión. Las vistas siempre usan ese grupo para validar.

## Flujo completo

1. **User tiene N grupos** (ej: Group A, Group B)
2. **Al login**: se elige el primer grupo activo → `request.session['group'] = group_id`
3. **En la vista**: PermissionMixin verifica `request.session['group']` tiene el módulo + permiso
4. **Si cambia de grupo**: logout y re-login con nuevo grupo (no hay switch en UI)

## Registrar un CRUD como Module

En `core/security/management/commands/insert_data.py`:

```python
MODULES = [
    {
        'type': 'Catálogos',
        'name': 'Empresas',
        'url': '/catalog/company/',
        'icon': 'fas fa-building',
        'description': 'Gestión de empresas',
        'permits_app': 'catalog',          # ← app del modelo
        'permits_model': 'company',        # ← nombre del modelo
        'order': 1,
    },
]
```

**¿Qué hace?**
- Crea `ModuleType` "Catálogos" si no existe
- Crea `Module` "Empresas"
- **Automáticamente genera 4 permisos:**
  - `view_catalog_company`
  - `add_catalog_company`
  - `change_catalog_company`
  - `delete_catalog_company`

(Django genera estos automáticamente al hacer makemigrations.)

## Asignar permisos a un grupo

**En la UI de admin:**
1. Ve a `Dashboard` → `Grupos`
2. Edita un grupo (ej: "Supervisor")
3. En `Módulos del grupo`, selecciona "Empresas"
4. Elige qué permisos tiene ese grupo en ese módulo

**En la BD (si lo necesitas hacer con insert_data.py):**
```python
group = Group.objects.get(name='Supervisor')
module = Module.objects.get(name='Empresas')
gm = GroupModule.objects.create(group=group, module=module)
gp1 = GroupPermission.objects.create(
    group_module=gm,
    permission=Permission.objects.get(codename='view_company'),
)
gp2 = GroupPermission.objects.create(
    group_module=gm,
    permission=Permission.objects.get(codename='change_company'),
)
```

## Código: PermissionMixin

```python
# core/security/mixins.py
class PermissionMixin(LoginRequiredMixin):
    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        # Si es superuser, bypass todo
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        # Si no está logueado, LoginRequiredMixin lo redirige
        
        # Valida permiso específico
        if self.permission_required:
            if not request.user.check_permission(
                self.permission_required,
                request.session.get('group')
            ):
                raise PermissionDenied()
        
        return super().dispatch(request, *args, **kwargs)
```

(Implementación real puede variar, pero la idea es igual.)

## Permisos por vista

| Vista | `permission_required` |
|-------|---------------------|
| XxxListView | `view_xxx` |
| XxxCreateView | `add_xxx` |
| XxxUpdateView | `change_xxx` |
| XxxDeleteView | `delete_xxx` |

```python
class CompanyListView(PermissionMixin, TemplateView):
    permission_required = 'view_company'

class CompanyCreateView(PermissionMixin, CreateView):
    permission_required = 'add_company'

class CompanyUpdateView(PermissionMixin, UpdateView):
    permission_required = 'change_company'

class CompanyDeleteView(PermissionMixin, DeleteView):
    permission_required = 'delete_company'
```

## Botones "Crear" / "Editar" / "Borrar" en templates

**Cómo NO mostrar botones si el usuario no tiene permiso:**

Opción 1: **Dejar que PermissionMixin cierre** — botones siempre visibles, pero 403 si intenta
Opción 2: **Validar en template** (raro, casi no se usa)

```html
<!-- En template: casi nunca se valida aquí -->
{% if request.user.is_superuser %}
    <a href="{% url 'company_create' %}" class="btn btn-primary">Crear</a>
{% else %}
    <!-- Déjalo visible, que intente y vea el 403 -->
    <a href="{% url 'company_create' %}" class="btn btn-primary">Crear</a>
{% endif %}
```

**Mejor:** no ocultes botones en template. El backend cierra. Si es incómodo para UX, el admin ajusta permisos.

## Debugging permisos

**"Por qué no puedo acceder a X?"**

1. ¿Estás logueado? → Sí
2. ¿Eres superuser? → Si sí, tienes acceso total
3. ¿Tu grupo tiene el módulo? → Ve a Grupos en la UI, editá tu grupo, mira "Módulos"
4. ¿Tu grupo tiene el permiso específico? → En el mismo lugar, mira "Permisos de [módulo]"
5. ¿Recargaste la página después de cambiar permisos? → Sí

Si nada funciona:
```python
# En Django shell
from core.security.models import Group, GroupPermission
from django.contrib.auth.models import Permission

# Verifica permisos del grupo
group = Group.objects.get(name='Tu Grupo')
for gm in group.groupmodule_set.all():
    print(f"Módulo: {gm.module.name}")
    for gp in gm.grouppermission_set.all():
        print(f"  - {gp.permission.codename}")
```

## Caso: agregar permiso a módulo existente

Si ya existe un módulo y quieres agregar un permiso:

```python
from core.security.models import GroupModule, GroupPermission
from django.contrib.auth.models import Permission

# 1. Obtén el módulo
module = Module.objects.get(name='Empresas')

# 2. Para cada grupo que lo tiene, agrega el permiso
for group_module in module.groupmodule_set.all():
    perm = Permission.objects.get(codename='add_company')
    GroupPermission.objects.get_or_create(
        group_module=group_module,
        permission=perm
    )
```

O en `insert_data.py` si es un nuevo módulo.

## Testing permisos

```python
from django.test import TestCase, Client
from django.contrib.auth.models import Permission

class CompanyPermissionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test', password='test')
        self.group = Group.objects.create(name='Supervisor')
        self.user.groups.add(self.group)

    def test_view_without_permission(self):
        self.client.login(username='test', password='test')
        response = self.client.get('/catalog/company/')
        self.assertEqual(response.status_code, 403)

    def test_view_with_permission(self):
        # Dale permiso al grupo
        perm = Permission.objects.get(codename='view_company')
        module = Module.objects.create(name='Empresas', ...)
        gm = GroupModule.objects.create(group=self.group, module=module)
        GroupPermission.objects.create(group_module=gm, permission=perm)
        
        self.client.login(username='test', password='test')
        response = self.client.get('/catalog/company/')
        self.assertEqual(response.status_code, 200)
```

---

**Fuente:** `CLAUDE.md` + código de `core/security/`.
