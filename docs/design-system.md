# ZAFIRA Web Design Guidelines

Guía base para diseños web de ZAFIRA. Puede usarse como referencia de UI o como brief para herramientas de diseño tipo Stitch.

## 1. Identidad Visual

| Token | Hex | Uso |
|---|---|---|
| Primary | `#FF3BBE` | Acciones principales, botones, highlights |
| Secondary | `#8E54FF` | Acciones secundarias, acentos y estados activos |
| Obsidian | `#0B0B0F` | Fondos oscuros, navegación y sombras profundas |
| Neutral | `#94A3B8` | Texto secundario, bordes y estados deshabilitados |

Usar gradientes solo en acciones principales o superficies destacadas. Evitar que toda la interfaz dependa de un único degradado.

## 2. Tipografía

- Fuente recomendada: Plus Jakarta Sans.
- Todo texto visible debe estar en español.
- Títulos: claros, breves y con peso alto.
- Texto de cuerpo: legible, con contraste suficiente.
- Labels y ayudas: compactos, sin saturar formularios.

Textos esperados en español:
- Botones.
- Estados vacíos.
- Errores de validación.
- Placeholders.
- Mensajes de carga.
- Confirmaciones.

## 3. Layout Web

- Priorizar vistas funcionales antes que páginas tipo landing.
- Usar navegación clara, persistente y fácil de escanear.
- En dashboards, preferir densidad controlada: tablas, filtros, acciones rápidas y estados visibles.
- En formularios, agrupar campos por intención y mantener acciones principales al final.
- Mantener espaciado consistente entre secciones, toolbars, tablas y formularios.
- Evitar tarjetas dentro de tarjetas.

## 4. Componentes

### Botones

- Primario: gradiente `#FF3BBE` a `#8E54FF`.
- Secundario: borde o fondo neutro con acento violeta.
- Estados: normal, hover, focus, disabled y loading.
- Los botones deben tener texto corto y acción clara.

### Inputs

- Placeholder en español.
- Focus con borde/acento primary.
- Error con borde rojo/pink y mensaje específico.
- Ayuda contextual solo cuando reduzca ambigüedad real.

Ejemplos:
- `Ingrese su usuario`
- `Ingrese su contraseña`
- `Seleccione un estado`
- `El correo ya se encuentra registrado`

### Tablas

- Columnas alineadas por tipo de dato.
- Acciones con iconos reconocibles.
- Estados activos/inactivos con badges.
- Filtros visibles cuando sean parte del flujo frecuente.

### Cards

- Usarlas para elementos repetidos o métricas concretas.
- Radio moderado y sombra suave.
- No usarlas como contenedor universal de secciones.

## 5. Estados UX

Mensajes estándar:

- Login/carga: `Iniciando sesión...`
- Redirección: `Redirigiendo a la página de inicio...`
- Registro exitoso: `Cuenta creada correctamente`
- Error de credenciales: `Usuario o contraseña incorrectos`
- Error genérico: `No se pudo completar la acción`

Todo flujo asíncrono debe tener estado de carga, éxito y error.

## 6. Iconografía

- Usar iconos simples y consistentes.
- Preferir iconos de librería antes que SVG manual.
- Acciones frecuentes:
  - Perfil: usuario/persona.
  - Módulos: grid/capas.
  - Guardado: bookmark.
  - Editar: lápiz.
  - Eliminar: trash.
  - Estado activo: check/circle.

## 7. Pantallas Base

### Login

- Formulario centrado en desktop y mobile.
- Fondo sobrio, con marca presente.
- Validación visible y mensajes en español.

### Dashboard

- Módulos agrupados por tipo.
- Accesos claros y consistentes.
- Estados vacíos cuando el grupo no tenga módulos disponibles.

### CRUD

- Lista con búsqueda, paginación y acciones.
- Crear/editar con el mismo patrón visual.
- Eliminar con confirmación explícita.
- Cambios de estado con confirmación corta.

## 8. Responsive

- Desktop: priorizar escaneo, comparación y acciones rápidas.
- Tablet: conservar navegación y reducir columnas si hace falta.
- Mobile: formularios y acciones en una sola columna.

El diseño debe adaptarse sin solapar texto, botones o iconos.
