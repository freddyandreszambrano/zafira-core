# Architecture

## Estructura

```text
ZAFIRA-CORE/
├── ai/              # Contexto mínimo para agentes IA
├── core/            # Apps Django
├── config/          # Settings, URLs, WSGI/ASGI
├── deploy/          # Archivos de despliegue
├── docs/            # Documentación técnica
├── requirements/    # Dependencias por entorno
├── scripts/         # Automatizaciones
├── static/          # Assets globales
├── templates/       # Bases compartidos
├── var/             # Runtime local ignorado por git
├── manage.py
├── Makefile
├── AGENTS.md
└── README.md
```

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

La base SQLite local vive en:

```text
var/db/db.sqlite3
```

`var/` no se versiona salvo `.gitkeep`.

