# Agent Policy

## Principios

- Leer `AGENTS.md` antes de cambiar código.
- Mantener `CLAUDE.md` como symlink hacia `AGENTS.md`.
- No revertir cambios ajenos ni limpiar archivos no relacionados.
- Priorizar patrones locales sobre abstracciones nuevas.
- Implementar cambios completos: código, verificación y resumen.

## Reglas de arquitectura

- `core/common/` no depende de ninguna app.
- Todo CRUD usa 4 views explícitas: list, create, update y delete.
- Toda view CRUD usa `PermissionMixin`.
- Los templates específicos viven dentro de su app.
- JavaScript específico vive en `core/<app>/static/<entity>/js/`.
- No usar JS inline en templates de entidad.

## Reglas de UI

- Usar Tailwind CSS y los tokens visuales globales de `templates/base.html`.
- Mantener soporte claro/oscuro con `color-scheme`, tokens CSS y clases `dark:`.
- No crear paletas de un solo tono; ZAFIRA usa contraste entre magenta, violeta, slate y superficies neutras.
- Los formularios deben usar estilos consistentes de campo, foco, borde y estados.
- Las tablas deben conservar el patrón DataTables centralizado con `Zafira.dataTable`.

## Verificación mínima

- Ejecutar pruebas relevantes cuando el cambio toque lógica Python.
- Revisar visualmente desktop y mobile cuando el cambio toque UI.
- Revisar contraste, foco visible y legibilidad en modo oscuro.

