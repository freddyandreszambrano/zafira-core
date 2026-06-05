# Archivos de Raíz

La raíz debe quedarse pequeña. Estos archivos permanecen ahí porque herramientas externas los buscan en esa ubicación o porque son puntos de entrada del proyecto.

## Puntos de entrada

| Archivo | Motivo |
|---|---|
| `README.md` | Entrada principal para humanos y repositorios remotos |
| `AGENTS.md` | Symlink a `ai/AGENTS.md`; requerido para auto-descubrimiento de agentes |
| `CLAUDE.md` | Symlink a `AGENTS.md` para compatibilidad con Claude |
| `Makefile` | Comandos operativos del proyecto |
| `manage.py` | CLI estándar de Django |

## Configuración de herramientas

| Archivo | Motivo |
|---|---|
| `pyproject.toml` | Configuración Python: black, isort, ruff, pytest y coverage |
| `package.json` | Scripts de Tailwind CSS |
| `package-lock.json` | Lockfile de dependencias npm |
| `.editorconfig` | Estilo común de editor |
| `.gitignore` | Exclusiones de Git |
| `.gitattributes` | Reglas de atributos Git |
| `.gitmessage` | Plantilla sugerida de commits |
| `.dockerignore` | Exclusiones del build Docker |
| `.env.example` | Plantilla de variables de entorno |

## Carpetas de herramientas

| Carpeta | Motivo |
|---|---|
| `.github/` | Workflows de CI y automatización |
| `.cursor/` | Reglas compartidas para Cursor |
| `dev/` | Configuración de herramientas de desarrollo |

## Carpetas principales

| Carpeta | Contenido |
|---|---|
| `core/` | Apps Django |
| `config/` | Settings, URLs, WSGI/ASGI y configuración de BD |
| `templates/` | Bases HTML compartidas |
| `static/` | Assets globales |
| `requirements/` | Dependencias por entorno |
| `deploy/` | Docker y despliegue |
| `docs/` | Documentación técnica |
| `scripts/` | Automatizaciones locales |
| `ai/` | Contexto y gobernanza para asistentes IA |

## Archivos locales ignorados

| Archivo o carpeta | Motivo |
|---|---|
| `.env` | Secretos y configuración local |
| `db.sqlite3` | Base SQLite local |
| `media/` | Archivos subidos localmente |
| `staticfiles/` | Salida de `collectstatic` |
| `node_modules/` | Dependencias npm |
| `__pycache__/` | Caché Python |
| `.idea/` | Configuración local de IDE |
| `.agents/` | Estado local de asistentes IA |
| `.codex/` | Estado local de Codex |
| `.python-version` | Versión local opcional de pyenv |
