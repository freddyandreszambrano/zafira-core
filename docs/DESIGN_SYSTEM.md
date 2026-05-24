# ZAFIRA Design System — Guía para Desarrolladores

Esta guía documenta los colores, utilidades y patrones de UI para mantener la consistencia visual de **ZAFIRA** en todas las plantillas del proyecto.

> Stack actual: **Tailwind CSS vía CDN** + **Font Awesome 6.4**. La configuración de marca está centralizada en `templates/base.html`.

---

## 1. Paleta de Colores

| Token | Hex | Uso |
|---|---|---|
| `zafira-primary` | `#FF3BBE` | Acción principal, botones primarios, highlights (Cyber-Magenta) |
| `zafira-primary-soft` | `#FFE5F6` | Fondos sutiles, badges, hover de filas |
| `zafira-primary-mid` | `#FFB6E2` | Estados intermedios, borders suaves |
| `zafira-secondary` | `#8E54FF` | Acción secundaria, acentos (Electric-Violet) |
| `zafira-secondary-soft` | `#EFE7FF` | Fondos sutiles violeta |
| `zafira-secondary-mid` | `#C2A8FF` | Estados intermedios violeta |
| `zafira-obsidian` | `#090101` | Texto enfático, fondos oscuros, sombras de tarjeta |
| `zafira-obsidian-soft` | `#1F1F23` | Variante suave del obsidian |
| `zafira-slate` | `#94A3BB` | Texto secundario, bordes, placeholders, estados disabled |
| `zafira-slate-soft` | `#E2E8F0` | Dividers, fondos de tabla |
| `zafira-slate-deep` | `#475569` | Texto de cuerpo (mejor contraste que `slate`) |

---

## 2. Configuración de Tailwind

La configuración se inyecta vía CDN en `templates/base.html` para que esté disponible en todas las plantillas:

```html
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          zafira: {
            primary: '#FF3BBE',
            'primary-soft': '#FFE5F6',
            'primary-mid': '#FFB6E2',
            secondary: '#8E54FF',
            'secondary-soft': '#EFE7FF',
            'secondary-mid': '#C2A8FF',
            obsidian: '#090101',
            'obsidian-soft': '#1F1F23',
            slate: '#94A3BB',
            'slate-soft': '#E2E8F0',
            'slate-deep': '#475569'
          }
        },
        boxShadow: {
          'zafira': '0 10px 30px -10px rgba(255, 59, 190, 0.35)',
          'zafira-lg': '0 20px 45px -15px rgba(255, 59, 190, 0.45)',
          'zafira-violet': '0 10px 30px -10px rgba(142, 84, 255, 0.35)'
        }
      }
    }
  }
</script>
```

> No modifiques esta config en plantillas hijas. Si necesitas un nuevo token, agrégalo aquí y documéntalo en este archivo.

---

## 3. Utilidades CSS Personalizadas

Definidas en `<style>` dentro de `templates/base.html`:

| Clase | Efecto |
|---|---|
| `.gradient-primary` | Fondo gradient `#FF3BBE → #8E54FF` (135°) |
| `.gradient-dark` | Fondo gradient obsidian `#090101 → #1F1F23` |
| `.gradient-soft` | Fondo gradient suave `primary-soft → secondary-soft` |
| `.zafira-text-gradient` | Texto con gradient primary→secondary (clip) |
| `.zafira-glow` | Hover con halo magenta + sombra |
| `.zafira-glow-violet` | Hover con halo violeta + sombra |
| `.zafira-border-gradient` | Border con gradient (útil como acento) |

---

## 4. Patrones de Componentes

### Botón Primario
```html
<a class="gradient-primary zafira-glow text-white font-bold px-6 py-3 rounded-xl
          flex items-center justify-center transition-transform hover:-translate-y-0.5">
  <i class="fas fa-users-cog mr-2"></i>Administrar Usuarios
</a>
```

### Botón Secundario (outline)
```html
<a class="bg-white border-2 border-zafira-primary text-zafira-primary font-bold
          px-6 py-3 rounded-xl hover:bg-zafira-primary-soft transition-colors">
  <i class="fas fa-user-plus mr-2"></i>Crear Usuario
</a>
```

### Card de Estadística
```html
<div class="bg-white rounded-2xl shadow-md hover:shadow-zafira transition-all duration-300
            p-6 border-l-4 border-zafira-primary group">
  <div class="flex items-center justify-between">
    <div>
      <p class="text-zafira-slate text-sm font-semibold uppercase tracking-wide">Total</p>
      <p class="text-4xl font-bold zafira-text-gradient mt-2">{{ value }}</p>
    </div>
    <div class="bg-zafira-primary-soft p-4 rounded-2xl group-hover:scale-110 transition-transform">
      <i class="fas fa-users text-zafira-primary text-2xl"></i>
    </div>
  </div>
</div>
```

### Badge de Estado
```html
<!-- Activo -->
<span class="px-3 py-1 text-xs font-semibold rounded-full
             bg-zafira-primary-soft text-zafira-primary inline-flex items-center">
  <i class="fas fa-check-circle mr-1"></i>Activo
</span>

<!-- Inactivo -->
<span class="px-3 py-1 text-xs font-semibold rounded-full
             bg-zafira-slate-soft text-zafira-slate-deep inline-flex items-center">
  <i class="fas fa-times-circle mr-1"></i>Inactivo
</span>
```

### Header de Sección (table / panel)
```html
<div class="px-6 py-4 gradient-primary">
  <h2 class="text-xl font-bold text-white flex items-center">
    <i class="fas fa-history mr-3"></i>Título de la sección
  </h2>
</div>
```

### Título de Página con Icono
```html
<h1 class="text-4xl font-bold flex items-center">
  <span class="inline-flex items-center justify-center w-12 h-12 rounded-xl
               gradient-primary shadow-zafira mr-4">
    <i class="fas fa-chart-line text-white text-xl"></i>
  </span>
  <span class="zafira-text-gradient">Dashboard</span>
</h1>
```

---

## 5. Reglas de Uso

1. **Usa siempre los tokens `zafira-*`** en vez de colores hardcoded (`#FF3BBE`) o paletas genéricas de Tailwind (`purple-600`, `green-500`).
2. **El texto principal** va en `text-zafira-obsidian` y el secundario en `text-zafira-slate-deep`. Reserva `text-zafira-slate` para placeholders, labels uppercase y estados deshabilitados.
3. **Los gradients** (primary→secondary) se reservan para elementos de alta jerarquía: nav, botones primarios, headers de sección, números destacados.
4. **Hover de filas / cards**: usa `hover:bg-zafira-primary-soft/40` (con opacidad) para no saturar.
5. **Sombras**: `shadow-zafira` para acentos magenta, `shadow-zafira-violet` para violeta, `shadow-md` para neutral.
6. **Rounded corners**: `rounded-xl` (botones, cards pequeñas), `rounded-2xl` (cards grandes, paneles), `rounded-full` (badges, avatares).
7. **Textos en español**: todo el copy visible para el usuario debe estar en español (botones, mensajes, placeholders, vacíos).

---

## 6. Referencia Cruzada

- **Definición completa de la marca** (tipografía, iconografía, mobile-first, dark mode, UX states): `docs/stich/DESIGN.md`
- **Implementación base** (config Tailwind + utilities): `templates/base.html`
- **Ejemplo de aplicación**: `templates/shared/dashboard/home.html`

---

## 7. Cómo agregar un nuevo color o utility

1. Edita la config en `templates/base.html` (sección `tailwind.config`).
2. Si es una utility CSS, agrégala en el bloque `<style>` del mismo archivo.
3. Documenta el nuevo token en la tabla de **§1 Paleta** o **§3 Utilidades** de este archivo.
4. Si introduce un nuevo patrón visual reutilizable, súmalo a **§4 Patrones de Componentes**.
