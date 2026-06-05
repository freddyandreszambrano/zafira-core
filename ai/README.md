# ZAFIRA-CORE AI Workspace

Esta carpeta organiza el contexto operativo para agentes IA que colaboren en el proyecto.

## Estructura

- `governance/`: reglas obligatorias, límites y convenciones del proyecto.
- `context/`: resumen funcional y técnico para onboarding rápido.
- `standards/`: estándares de desarrollo, UI, pruebas y documentación.
- `prompts/`: prompts reutilizables para tareas frecuentes.
- `workflows/`: checklists de ejecución para cambios comunes.

## Fuente de verdad

`AGENTS.md` sigue siendo la guía raíz del repositorio. Los documentos en `ai/` la complementan y no deben contradecirla.

Cuando haya conflicto, este es el orden de prioridad:

1. Instrucciones explícitas del usuario en la sesión actual.
2. `AGENTS.md`.
3. Documentos dentro de `ai/governance/`.
4. Documentos de `ai/context/`, `ai/standards/`, `ai/prompts/` y `ai/workflows/`.

