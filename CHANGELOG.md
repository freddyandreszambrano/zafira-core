# Changelog

Todos los cambios notables del proyecto se documentan aquí.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Added
- Tooling: `.editorconfig`, `.gitattributes`, `.python-version`, `.gitmessage`
- Linters unificados en `pyproject.toml` (black, isort, ruff, pytest)
- Pre-commit hooks (`.pre-commit-config.yaml`)
- Cursor IDE rules (`.cursor/rules/project.mdc`)
- GitHub Actions CI (`.github/workflows/ci.yml`)
- Docker stack (`deploy/docker/Dockerfile`, `deploy/docker/docker-compose.yml`, `.dockerignore`)
- AI PR reviewer (`scripts/pr_review/`)

### Changed
- `CLAUDE.md` ahora es symlink a `AGENTS.md` (dedupe del manual de IA)

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
- Makefile con 27 targets
- Documentación de gobernanza en `docs/governance/`
