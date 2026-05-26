# Comandos Make

Comandos útiles para desarrollo.

## Setup y corridas

| Comando | Para qué | Cuándo |
|---------|----------|--------|
| `make setup` | Install + migrate + insert-data | Primera vez que clonas |
| `make run` | Levanta server en `0.0.0.0:8000` | Cada vez que quieras desarrollar |
| `make runserver` | Alias de `make run` | (mismo) |

## Migraciones

| Comando | Para qué | Cuándo |
|---------|----------|--------|
| `make makemigrations` | Genera migraciones de cambios en `models.py` | Después de tocar modelo |
| `make migrate` | Aplica migraciones | Después de `makemigrations` |
| `make reset-db` | ⚠ Borra `db.sqlite3` y recrea desde cero | Si la BD queda en estado inconsistente |

## Datos

| Comando | Para qué | Cuándo |
|---------|----------|--------|
| `make insert-data` | Carga módulos + admin/admin (seed) | Después de `migrate` |
| `make resetfull` | `reset-db` + `migrate` + `insert-data` | Reset total |

## Testing

| Comando | Para qué | Cuándo |
|---------|----------|--------|
| `make test` | Corre todos los tests | Antes de mergear |
| `make test-fast` | Corre tests reusando BD anterior | Desarrollo iterativo |

## Limpieza

| Comando | Para qué | Cuándo |
|---------|----------|--------|
| `make kill-python` | Mata procesos Python que lockean la BD | BD queda locked (WSL/Windows) |
| `make clean` | Borra `*.pyc`, `__pycache__`, `.coverage` | Limpieza general |

## Otras

| Comando | Para qué | Cuándo |
|---------|----------|--------|
| `make help` | Lista todos los comandos | ¿No recuerdas qué hay? |
| `make shell` | Django shell interactivo | Queries manuales, debugging |
| `make createsuperuser` | Crea usuario admin | Si borras el anterior |

## Workflow típico (desarrollo)

```bash
# Primera vez
make setup      # instala todo, crea BD, carga seed

# Cada vez que abres una sesión
make run        # levanta server

# Después de tocar un modelo
make makemigrations
make migrate

# Después de agregar un CRUD nuevo
make insert-data  # (o manualmente en la UI)

# Antes de mergear
make test       # verifica todo funciona

# Si algo anda mal
make kill-python  # desbloquea BD
# O:
make resetfull    # BD limpia desde cero
```

## Problemas comunes

### "Error: database is locked"

```bash
make kill-python
# O:
make reset-db
```

**Causa:** En WSL o Windows con Python + SQLite, los locks a veces quedan. Mata el proceso Python o resetea la BD.

### "¿Por qué no ve mi modelo nuevo?"

```bash
make makemigrations
make migrate
# Luego reload en el navegador
```

**Causa:** Hiciste cambios a `models.py` pero no corriste migraciones.

### "Quiero resetear todo"

```bash
make resetfull
make run
```

**Resultado:** BD limpia, seed cargado, usuario `admin/admin` disponible.

### "¿Dónde está el Makefile?"

En la raíz del proyecto:
```bash
cat Makefile  # para ver todos los targets
```

---

**Pro tip:** `make help` te lista todo. `make test-fast` es tu amigo durante desarrollo iterativo.
