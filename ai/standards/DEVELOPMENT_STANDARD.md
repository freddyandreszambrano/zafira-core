# Development Standard

## Código

- Imports al inicio del archivo.
- Evitar docstrings obvios.
- Mantener archivos por debajo de unas 200 líneas cuando sea razonable.
- Dividir paquetes grandes en `models/`, `views/`, `forms/` y `tests/`.
- Usar `TextChoicesCustom` para choices de dominio.
- Usar widgets de `core.common.forms.widgets` y constantes de `core.common.constants`.

## CRUD

- List: `search` y `change_state`.
- Create: `add` y `validate_data`.
- Update: `edit` y `validate_data`, excluyendo el objeto actual en validaciones únicas.
- Delete: POST directo con JSON.
- Cada entidad debe tener `to_json()` si se lista por DataTables.

## Frontend

- Base compartida: `templates/base.html`, `templates/list.html`, `templates/form.html`, `templates/delete.html`.
- Entidad: `core/<app>/templates/<entity>/...`.
- JavaScript de entidad: `core/<app>/static/<entity>/js/list.js` y `form.js`.
- Evitar templates passthrough si solo extienden el base y no agregan bloques.
- Usar botones con iconos para acciones de tabla y herramientas.

## Modo oscuro

- Declarar `meta name="color-scheme"` en layouts base.
- Usar tokens CSS globales para fondo, superficie, borde y texto.
- Evitar dark mode negro puro en superficies grandes.
- Mantener contraste de texto normal de al menos 4.5:1.
- Mantener foco visible con contraste suficiente.

