# Project Brief

ZAFIRA-CORE es un sistema administrativo Django donde los módulos del dashboard se configuran desde base de datos. El objetivo del producto es permitir activar, ordenar y controlar secciones del menú sin tocar código.

## Stack

- Django 5.2 y Django REST Framework.
- SQLite en desarrollo y PostgreSQL en producción.
- Tailwind CSS, DataTables y FormValidation en frontend.
- `django-crum` para request actual desde modelos.
- `django-widget-tweaks` para renderizar formularios.

## Dominios principales

- `security`: módulos, tipos de módulo, grupos, permisos dinámicos.
- `auth`: usuario custom, login, registro, dashboard, perfil y CRUD de usuarios.
- `profiles`: datos extendidos del usuario.
- `scraper`: herramienta temporal de extracción de productos.
- `common`: choices, constantes, widgets y mixins compartidos.

## Experiencia objetivo

El producto debe sentirse como una herramienta administrativa profesional: densa pero clara, con navegación predecible, tablas escaneables, formularios sobrios y modo oscuro cómodo para uso prolongado.

