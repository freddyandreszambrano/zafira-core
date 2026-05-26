# ZAFIRA-CORE — Gobernanza para Claude

Cuando uses Claude en este proyecto, **lee primero** los documentos en esta carpeta. Definen cómo Claude debe entender y trabajar con el código.

## Índice rápido

| Documento | Para qué |
|-----------|----------|
| [**claude-guide.md**](claude-guide.md) | Cómo briefear a Claude y obtener mejores resultados |
| [**ESTRUCTURA**](structure/) | Carpetas, archivos, naming: anatomía del proyecto |
| [**PATRONES**](patterns/) | CRUD, views, forms, templates: cómo escribir código aquí |
| [**REGLAS**](rules/) | Errores a evitar, convenciones, sistema de permisos |
| [**QUICK START**](quick-start.md) | Primeros pasos para un dev nuevo en el proyecto |

## Lo más importante

**Este es un proyecto Django con módulos configurables en BD.** El patrón es:
- **4 views explícitas** por CRUD (`List/Create/Update/Delete`), cada una con su `post()` inline
- **Templates y JS organizados por entidad** dentro de cada app
- **Sin clases base "CrudXxxView"** — repetición controlada es mejor que abstracción genérica
- **PermissionMixin en toda vista CRUD** para validar permisos dinámicos
- **Imports al top**, sin docstrings obvios, modularización agresiva

## El archivo "Biblia"

**`CLAUDE.md`** en la raíz del repo es la fuente de verdad. Los docs aquí lo desglosan.

## Workflow típico

1. **Usuario pide feature/fix** → Claude lee `CLAUDE.md` + archivos relevantes
2. **Claude plantea enfoque** → usuario aprueba
3. **Claude implementa** → sigue patrones de CRUD/views/forms/templates
4. **Tests, lint, review** → antes de mergear

## Para preguntas

- ¿Cómo agrego un CRUD? → [**patterns/crud.md**](patterns/crud.md)
- ¿Dónde va este archivo?  → [**structure/folders.md**](structure/folders.md)
- ¿Qué nombre le doy?       → [**structure/naming.md**](structure/naming.md)
- ¿Qué NO debo hacer?       → [**rules/do-and-dont.md**](rules/do-and-dont.md)

---

**Última actualización:** 2026-05-26  
**Responsable:** Freddy (dev principal)
