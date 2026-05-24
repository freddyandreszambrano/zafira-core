---
name: Zafira
colors:
  surface: '#041426'
  surface-dim: '#041426'
  surface-bright: '#2b3a4e'
  surface-container-lowest: '#010f21'
  surface-container-low: '#0d1c2f'
  surface-container: '#112033'
  surface-container-high: '#1c2b3e'
  surface-container-highest: '#273649'
  on-surface: '#d4e3fd'
  on-surface-variant: '#debecc'
  inverse-surface: '#d4e3fd'
  inverse-on-surface: '#233145'
  outline: '#a68996'
  outline-variant: '#58404c'
  surface-tint: '#ffaed8'
  primary: '#ffaed8'
  on-primary: '#610045'
  primary-container: '#ff3bbe'
  on-primary-container: '#55003c'
  inverse-primary: '#b30083'
  secondary: '#d2bcff'
  on-secondary: '#3e008f'
  secondary-container: '#5b02cc'
  on-secondary-container: '#c5aaff'
  tertiary: '#e0bfbc'
  on-tertiary: '#402b2a'
  tertiary-container: '#a88a88'
  on-tertiary-container: '#392524'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffd8e9'
  primary-fixed-dim: '#ffaed8'
  on-primary-fixed: '#3c0029'
  on-primary-fixed-variant: '#890063'
  secondary-fixed: '#eaddff'
  secondary-fixed-dim: '#d2bcff'
  on-secondary-fixed: '#24005a'
  on-secondary-fixed-variant: '#5900c7'
  tertiary-fixed: '#fedad8'
  tertiary-fixed-dim: '#e0bfbc'
  on-tertiary-fixed: '#291616'
  on-tertiary-fixed-variant: '#59413f'
  background: '#041426'
  on-background: '#d4e3fd'
  surface-variant: '#273649'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 28px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-margin: 1.5rem
  gutter: 1rem
  stack-sm: 0.5rem
  stack-md: 1rem
  stack-lg: 2rem
---

# ZAFIRA App Design Guidelines
## 1. Brand Colors
- Primary: #FF3BBE → main actions, buttons, highlights (Cyber-Magenta)
- Secondary: #8E54FF → secondary actions, accents (Electric-Violet)
- Tertiary: #090101 → ultra-dark backgrounds, card shadows (Obsidian)
- Neutral: #94A3BB → text, borders, disabled states (Cool Slate)
## 2. Typography
- Font: Plus Jakarta Sans
- Headline: Bold, large (emphasizing high-contrast impact)
- Body: Medium, readable (balanced for dark mode)
- Labels: Small, subtle contrast with 0.02em letter spacing
- **All text in designs must be in Spanish**, including:
  - Buttons
  - Error messages
  - Input placeholders
  - Loading or redirect messages
## 3. Components
- Buttons:
  - Primary gradient: #FF3BBE → #8E54FF
  - Rounded corners (8px default)
  - States: normal, pressed, hover (slight brightness change or glow effect)
- Inputs:
  - Placeholder in Spanish (e.g., "Ingrese su usuario", "Ingrese su contraseña")
  - Focus: border highlighted in primary color (#FF3BBE)
  - Error: pink border (#FF3BBE) + message in Spanish
- Links:
  - Secondary actions (e.g., "¿Olvidaste tu contraseña?", "Crear cuenta") in secondary purple tone
- Cards:
  - Rounded borders (0.5rem to 1rem), soft tonal layering
  - Centered on mobile screen for high focus
## 4. Layout
- Mobile-first
- Obsidian background (#090101) for maximum depth
- Cards for login and transitions centered
- Consistent spacing using the 8px base grid
- Maintain visual consistency across screens
## 5. UX Considerations
- Loading indicators for async actions using brand colors
- Clear error messages in Spanish
- Smooth transitions to Home screen
- Interactive states for buttons and inputs
## 6. Iconography
- Minimal icons for Google/Apple login
- Optional: subtle AI / virtual try-on motifs in background
- User menu icons:
  - Profile → person icon
  - AI Clothing → t-shirt/shirt icon
  - Saved → bookmark/heart icon
## 7. Screens / States
- Login normal
- Credential error (highlighted in #FF3BBE)
- Loading / logging in → message in Spanish: "Iniciando sesión…"
- Redirect → message in Spanish: "Redirigiendo a la página de inicio…"
- Account creation success → message in Spanish: "¡Cuenta creada con éxito!"
- User screen:
  - Shows profile info
  - Options: "Acerca de la app", "Editar datos"
  - Metrics: saved outfits, AI consumption
  - Bottom menu with icons (Profile, AI Clothing, Saved)