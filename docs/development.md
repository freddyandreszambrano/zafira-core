# Development

## Comandos

| Comando | Uso |
|---|---|
| `make help` | Lista comandos disponibles |
| `make setup` | Instala, migra y carga seed |
| `make run` | Levanta servidor local |
| `make check` | Ejecuta `manage.py check` |
| `make migrate` | Aplica migraciones |
| `make makemigrations` | Genera migraciones |
| `make insert-data` | Carga módulos y admin/admin |
| `make test` | Ejecuta tests |
| `make reset-db` | Borra `db.sqlite3` y recrea datos |

## CRUD

Cada CRUD usa 4 views explícitas:

- `XxxListView`: `search`, `change_state`.
- `XxxCreateView`: `add`, `validate_data`.
- `XxxUpdateView`: `edit`, `validate_data`.
- `XxxDeleteView`: POST directo.

Reglas:

- Toda view CRUD usa `PermissionMixin`.
- No crear clases base genéricas tipo `CrudView`.
- El modelo debe exponer `to_json()` si aparece en DataTables.
- Validaciones remotas responden `{valid: true|false}`.

## Ubicación de Archivos

| Elemento | Ubicación |
|---|---|
| Modelo | `core/<app>/models/<entity>.py` |
| Form | `core/<app>/forms/<entity>.py` |
| Views | `core/<app>/views/<entity>.py` |
| Templates | `core/<app>/templates/<entity>/` |
| JS | `core/<app>/static/<entity>/js/` |
| Tests | `core/<app>/tests/` |

## JavaScript

- `list.js`: DataTables y acciones de lista.
- `form.js`: FormValidation y validación remota.
- No usar JS inline en templates.
- Usar helpers globales de `Zafira` definidos en `templates/base.html`.

## Permisos

- List: `view_xxx`.
- Create: `add_xxx`.
- Update: `change_xxx`.
- Delete: `delete_xxx`.

`PermissionMixin` valida permisos contra el grupo activo en sesión.
