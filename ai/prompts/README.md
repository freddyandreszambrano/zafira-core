# Prompt Library

Prompts reutilizables para agentes IA. Copia solo el bloque que necesites y añade el contexto concreto de la tarea.

## Code Review

```text
Actúa como reviewer senior de ZAFIRA-CORE. Lee AGENTS.md y revisa el diff actual.
Prioriza bugs, regresiones, permisos, seguridad, tests faltantes y coherencia con el patrón CRUD explícito.
Entrega hallazgos con archivo y línea.
```

## Nuevo CRUD

```text
Lee AGENTS.md y crea un CRUD para <Entidad> en <app>.
Respeta el patrón de 4 views explícitas, PermissionMixin, templates app-locales, JS externo, DataTables y validate_data.
Actualiza insert_data.py si debe aparecer como módulo del dashboard.
```

## Auditoría UI

```text
Audita la UI de ZAFIRA-CORE en claro y oscuro.
Revisa contraste, bordes, foco visible, tablas, formularios, cards y navegación.
Aplica mejoras con Tailwind CSS y tokens globales sin romper patrones existentes.
```

