# AI Context

ZAFIRA-CORE es un sistema administrativo Django con dashboard y módulos configurables desde base de datos.

## Stack

- Django 5.2 y Django REST Framework.
- SQLite local en `var/db/db.sqlite3`.
- PostgreSQL para despliegue con Docker.
- Tailwind CSS vía CDN, DataTables y FormValidation.
- `django-crum` y `django-widget-tweaks`.

## Apps

- `core/common`: utilidades compartidas.
- `core/security`: módulos, grupos y permisos dinámicos.
- `core/auth`: autenticación, dashboard, perfil y usuarios.
- `core/profiles`: datos extendidos de usuario.
- `core/scraper`: herramientas de scraping.

## Documentación

- Reglas obligatorias: `AGENTS.md`.
- Arquitectura: `docs/architecture.md`.
- Desarrollo: `docs/development.md`.
- Diseño: `docs/design-system.md`.

