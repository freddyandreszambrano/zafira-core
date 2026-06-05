# UI Dark Mode Checklist

Usa esta lista cuando cambies layouts, formularios, tablas o dashboard.

## Antes de editar

- Revisar `templates/base.html`.
- Revisar si la pantalla extiende `base.html`, `list.html`, `form.html` o `delete.html`.
- Identificar clases Tailwind que no tienen variante `dark:`.
- Preferir tokens globales antes que colores hardcodeados.

## Durante la edición

- Usar `z-page` para fondos de páginas internas.
- Usar `z-card` para superficies principales.
- Usar `z-field` para inputs, selects y textareas.
- Usar `z-heading`, `z-soft` y `z-muted` para texto semántico.
- Mantener botones existentes `z-btn-primary` y `z-btn-ghost`.

## Verificación

- Probar tema claro y oscuro.
- Revisar que tablas DataTables mantengan header, filas, hover y paginación legibles.
- Revisar formularios con foco activo.
- Revisar mobile para sidebar y botones.
- Confirmar que no haya texto oscuro sobre fondo oscuro ni borde invisible.

