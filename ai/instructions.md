# AI Instructions

## Prioridad

1. Instrucciones del usuario.
2. `AGENTS.md`.
3. Documentos en `docs/`.
4. Este archivo.

## Reglas

- No crear carpetas o archivos `.md` si no tienen uso claro.
- Mantener nombres generales, en inglés y kebab-case para documentación.
- Seguir patrones existentes antes de crear abstracciones nuevas.
- No revertir cambios ajenos.
- Verificar con `python manage.py check` cuando el cambio toque Django.
- Para UI, usar los tokens globales definidos en `templates/base.html`.

## CRUD

- Usar 4 views explícitas: List, Create, Update y Delete.
- Usar `PermissionMixin` en toda view CRUD.
- Mantener JS de entidad en `core/<app>/static/<entity>/js/`.
- Mantener templates de entidad dentro de `core/<app>/templates/<entity>/`.

