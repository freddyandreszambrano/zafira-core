# Quick Start — Para Dev Nuevo

Acabas de clonar ZAFIRA-CORE. Estos son los primeros pasos.

## 1. Setup inicial (5 min)

```bash
make setup          # install + migrate + insert-data
make run            # levanta server en 0.0.0.0:8000
```

Accede a `http://localhost:8000` y login con `admin / admin`.

## 2. Lee la estructura (10 min)

```
core/
├── common/          ← Compartido: choices, constants, widgets, mixins
├── security/        ← Módulos y permisos dinámicos
├── auth/            ← Users, login, dashboard
└── profiles/        ← UserProfile (datos extendidos)

templates/           ← SOLO bases compartidos (list.html, form.html, delete.html, base.html)
static/              ← SOLO assets globales (CSS Tailwind, etc)
```

**Regla de oro:** cada CRUD vive dentro de su app: `core/<app>/templates/<entity>/` y `core/<app>/static/<entity>/js/`.

## 3. Entiende el patrón CRUD (15 min)

Cada CRUD = **4 views explícitas**:

```python
class XxxListView(PermissionMixin, TemplateView):
    permission_required = 'view_xxx'
    def post(self, request, ...):
        action = request.POST.get('action')
        if action == 'search':      # DataTable AJAX
            ...
        elif action == 'change_state':  # toggle is_active
            ...

class XxxCreateView(PermissionMixin, CreateView):
    permission_required = 'add_xxx'
    def post(self, request, ...):
        if action == 'add':         # guardar
        elif action == 'validate_data':  # validación en vivo

class XxxUpdateView(PermissionMixin, UpdateView):
    permission_required = 'change_xxx'
    # mismo patrón que Create

class XxxDeleteView(PermissionMixin, DeleteView):
    permission_required = 'delete_xxx'
    def post(self, request, ...):
        self.get_object().delete()
```

**No hay clases base "CrudXxxView"** — cada view es autocontenida, se lee linealmente.

## 4. Cómo pedir a Claude que agregue un feature

Cuando pidas a Claude que agregue un CRUD, di:

> Agrega un CRUD de `Company` en `core/catalog/`. Modelo: `name` (único), `is_active`. 
> Luego registra como Module en insert_data.py.

Claude sabrá automáticamente:
- Crear modelo → form → 4 views → templates (list/form/delete) → JS (list.js/form.js)
- Poner templates en `core/catalog/templates/company/`
- Poner JS en `core/catalog/static/company/js/`
- Registrar en insert_data
- Usar `PermissionMixin` con los permisos correctos

## 5. Comandos útiles

| Comando | Para qué |
|---------|----------|
| `make run` | Levanta server |
| `make migrate` | Corre migraciones pendientes |
| `make makemigrations` | Genera migraciones |
| `make insert-data` | Carga modules + admin/admin |
| `make test` | Corre tests |
| `make kill-python` | Si la BD queda locked (WSL/Windows) |

## 6. Próximos pasos

- **Lee `../CLAUDE.md`** → Gobernanza completa del proyecto
- **Explora `core/security/views/`** → Ejemplo real de CRUD
- **Ve `core/auth/static/user/js/form.js`** → Ejemplo de FormValidation complejo

---

**¿Duda?** Abre los docs en `docs/governance/` o pregunta al dev principal.
