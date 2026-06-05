# Architecture

## Estructura

```text
ZAFIRA-CORE/
├── ai/              # Contexto y gobernanza para agentes IA
├── config/          # Settings, URLs, WSGI/ASGI
├── core/            # Apps Django
├── dev/             # Configuración de herramientas de desarrollo
├── deploy/          # Archivos de despliegue
├── docs/            # Documentación técnica
├── requirements/    # Dependencias por entorno
├── scripts/         # Automatizaciones
├── static/          # Assets globales
├── templates/       # Bases compartidos
├── manage.py
├── Makefile
├── AGENTS.md        # Symlink a ai/AGENTS.md
├── CLAUDE.md        # Symlink a AGENTS.md
└── README.md
```

Ver [project/root-files.md](project/root-files.md) para el detalle de los archivos que permanecen en la raíz.

## Apps

- `core/common`: choices, constantes, widgets y mixins compartidos.
- `core/security`: módulos, grupos y permisos dinámicos.
- `core/auth`: usuario custom, login, dashboard, perfil y CRUD de usuarios.
- `core/profiles`: datos extendidos de usuario.
- `core/scraper`: herramientas de scraping.

## Templates

`templates/` raíz solo contiene bases compartidos:

- `base.html`
- `base_public.html`
- `list.html`
- `form.html`
- `delete.html`

Templates específicos viven en `core/<app>/templates/<entity>/`.

## Static

Assets globales viven en `static/`.

JS específico de entidad vive en:

```text
core/<app>/static/<entity>/js/
```

## Runtime

La base SQLite local se genera en:

```text
db.sqlite3
```

`db.sqlite3` no se versiona.
