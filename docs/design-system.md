# Design System

La UI usa Tailwind CSS vía CDN y tokens CSS globales en `templates/base.html`.

## Clases Globales

| Clase | Uso |
|---|---|
| `z-page` | Fondo estándar de páginas internas |
| `z-card` | Superficie/card |
| `z-field` | Inputs, selects y textareas |
| `z-heading` | Texto principal |
| `z-soft` | Texto secundario |
| `z-muted` | Texto auxiliar |
| `z-btn-primary` | Acción principal |
| `z-btn-ghost` | Acción secundaria |
| `z-table-card` | Contenedor de tablas |
| `z-badge` | Estado |
| `z-icon-btn` | Botón compacto con icono |

## Modo Oscuro

- Mantener `<meta name="color-scheme" content="light dark">`.
- Usar tokens CSS para fondos, superficies, bordes y texto.
- Evitar negro puro como superficie principal.
- Mantener foco visible en elementos interactivos.
- Revisar contraste en tablas, formularios y dashboard.

## Patrón de Página

```html
<div class="z-page py-10">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <section class="z-card p-6">
      <h1 class="z-heading">Título</h1>
    </section>
  </div>
</div>
```

