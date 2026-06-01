# Cómo Trabajar con Claude en ZAFIRA-CORE

Claude Code está integrado en el proyecto. Sigue estas reglas para obtener los mejores resultados.

## Antes de usar Claude

1. **Lee `CLAUDE.md`** en la raíz — es la fuente de verdad de todo
2. **Asume que Claude ya conoce el proyecto** — automáticamente cargará `CLAUDE.md` y la memoria compartida
3. **Sé específico en tu petición** — "agrega un CRUD de Company" es mejor que "necesito un nuevo modelo"

## Cómo pedir features

### ❌ Malo
> "Agrega una nueva sección en el dashboard"

### ✅ Bueno
> "Agrega un CRUD de `Company` (modelo: name, is_active) en `core/catalog/`. Registra como Module en insert_data.py. Usa el patrón List/Create/Update/Delete estándar de aquí."

### ✅ Mejor aún (si conoces el contexto)
> "Agrega `Company` en `core/catalog/` como CRUD estándar. Necesito:
> - Modelo con name (único) e is_active
> - Validación de nombre en vivo (FormValidation)
> - Toggle de estado en la lista
> - Registra en insert_data como Module tipo 'Catálogos'"

## Reglas de Claude en este proyecto

### ✅ Claude HARÁ

- Seguir el patrón **4 views explícitas** (List/Create/Update/Delete) sin clases base
- Poner **templates en `core/<app>/templates/<entity>/`** y **JS en `core/<app>/static/<entity>/js/`**
- Usar **PermissionMixin** en toda vista CRUD
- Escribir **código limpio**: sin docstrings obvios, modularizar agresivamente
- **Leer archivos existentes** para entender patrones antes de escribir
- **Ejecutar tests y verificar cambios** antes de decir que está listo
- **Respetar convenciones de naming**: snake_case en Python, camelCase en JS

### ❌ Claude NO HARÁ

- ❌ Crear clases base "CrudXxxView" para deduplicar
- ❌ Poner JS inline en templates
- ❌ Crear vistas AJAX separadas (las acciones van inline con `if/elif action == ...`)
- ❌ Hardcodear textos del UI en español dentro de modelos
- ❌ Introducir docstrings obvios (`"""Get user groups."""`)
- ❌ Poner templates/static en `templates/` o `static/` globales si son de entidad específica

## Peticiones comunes

### 1. "Agrega un nuevo módulo CRUD"

Cómo pedirlo:
```
Agrega un CRUD de `Product` en `core/catalog/`.

Modelo:
- name (CharField, unique)
- description (TextField, nullable)
- price (DecimalField)
- is_active (BooleanField, default=True)

Incluye:
- Validación de nombre único en vivo
- Toggle de estado en la lista
- Búsqueda en tiempo real
- Registra como Module tipo "Catálogos" en insert_data

Sigue el patrón estándar: List/Create/Update/Delete views + templates/JS por entidad.
```

Claude entenderá automáticamente:
- Crear modelo + form + 4 views
- Poner templates en `core/catalog/templates/product/`
- Poner JS en `core/catalog/static/product/js/`
- Usar `PermissionMixin` + `product_view/add/change/delete`
- Registrar en insert_data

### 2. "Corrige un bug en X"

Cómo pedirlo:
```
En la lista de usuarios, cuando filtro por departamento, algunos usuarios desaparecen. 
Verifica:
1. La query en UserListView.post() cuando action='search'
2. El filtro de departamento en el JS

El error probablemente está en la query, no en el template.
```

Claude:
- Leerá los archivos relevantes
- Identificará la causa
- Corregirá y verificará que funcione
- Escribirá tests si es necesario

### 3. "Refactoriza / Mejora X"

Cómo pedirlo:
```
El módulo `core/auth/views/users.py` tiene mucha duplicación entre Create y Update.
Refactoriza para mejorar legibilidad, pero mantén las 4 views separadas (no crees clase base).

Después de refactorizar, corre los tests y confirma que sigue funcionando.
```

Claude:
- Mejorará el código sin cambiar la estructura
- Respetará la convención de views explícitas
- Verificará tests
- Reportará cambios

## Memoria compartida (para los compañeros)

Cada vez que uses Claude:
- **Tu trabajo en la branch se guarda automáticamente** en memoria
- Si vuelves mañana con la misma branch, Claude recordará el contexto
- Los docs en `docs/governance/` también se cargan

Esto significa: **puedes dejar un trabajo a mitad, volver después, y Claude continuará exactamente donde dejaste**.

## Workflow típico

1. **Pides feature** → Claude plantea enfoque
2. **Apruebas enfoque** → Claude implementa
3. **Claude verifica** → tests, lint, funcionalidad en app
4. **Mergeas a `develop`** (o `main` si es hotfix)

## Troubleshooting

### "Claude no sigue el patrón de CRUD"
→ Remindele: "Usa 4 views explícitas List/Create/Update/Delete sin clases base. Cada `post()` con `if/elif action == ...`"

### "Claude puso templates en la carpeta global"
→ Corrige: "Templates de entidad específica van en `core/<app>/templates/<entity>/`. Los globales (list.html, form.html, base.html) ya existen."

### "El JS está inline en el template"
→ Corrige: "JS va en archivo externo: `core/<app>/static/<entity>/js/`. Carga vía `{% static %}`."

### "Creó una clase base para deduplicar"
→ Corrige: "No uses clases base. Repetición controlada es mejor. Cada view es autocontenida y se lee linealmente."

## Links útiles

- [`CLAUDE.md`](../../CLAUDE.md) — Gobernanza canónica
- [`docs/governance/`](./) — Esta carpeta
- [`core/security/views/`](../../core/security/views/) — Ejemplo real de CRUD
- [`core/auth/views/`](../../core/auth/views/) — Más ejemplos

---

**Recuerda:** Claude es una herramienta. Las reglas aquí aseguran que el código sea consistente, legible y mantenible. 🚀
