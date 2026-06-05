# Changelog

Todos los cambios notables del proyecto se documentan aquí.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Added
- Tooling: `.editorconfig`, `.gitattributes`, `.gitmessage`
- Linters unificados en `pyproject.toml` (black, isort, ruff, pytest)
- Pre-commit hooks (`.pre-commit-config.yaml`)
- Cursor IDE rules (`.cursor/rules/project.mdc`)
- GitHub Actions CI (`.github/workflows/ci.yml`)
- Docker stack (`deploy/docker/Dockerfile`, `deploy/docker/docker-compose.yml`, `.dockerignore`)
- AI PR reviewer (`scripts/pr_review/`)

### Changed
- `CLAUDE.md` ahora es symlink a `AGENTS.md` (dedupe del manual de IA)
- Configuración de base de datos alineada con BACKOFFICE: `config/db.py`, `PSQL=0|1` y SQLite local en `db.sqlite3`
- `Makefile` reestructurado por secciones con comentarios visuales
- Gobernanza IA movida a `ai/AGENTS.md`; `AGENTS.md` y `CLAUDE.md` quedan como symlinks de compatibilidad
- Configuración de pre-commit movida a `dev/pre-commit-config.yaml`
- `.python-version` removido del repo; queda como archivo local opcional

## [0.1.0] - 2026-06-05

### Added
- Sistema dinámico de Módulos (app `security`): `Module`, `ModuleType`, `Group`, `GroupModule`, `GroupPermission`
- Custom `User` model con sesión de grupo activa (`set_group_session`, `get_group_id_session`)
- CRUD de Users con permisos por grupo (`PermissionMixin`)
- Dashboard con tarjetas agrupadas por `ModuleType`
- Context processor `available_modules` para nav dinámico
- Patrón CRUD canónico: 4 views explícitas (`List/Create/Update/Delete`) con `post()` inline
- Templates y JS app-local por entidad (`<app>/templates/<entity>/`, `<app>/static/<entity>/`)
- Tailwind CSS 4 vía CDN + DataTables + FormValidation
- Management command `insert_data` (seed: módulos + grupo Admin + usuario `admin/admin`)
- Documentación de gobernanza en `AGENTS.md`
