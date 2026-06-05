# scripts/

Utilidades de desarrollo, CI y mantenimiento. Una subcarpeta por dominio.

## Convenciones

- **Python puro (stdlib)** siempre que se pueda — evita pip install en CI.
- Cada subcarpeta tiene su propio `README.md` con: propósito, requisitos, uso local, uso en CI.
- Variables sensibles solo vía env vars (no hardcodear).
- Scripts ejecutables tienen shebang `#!/usr/bin/env python3` y permisos `+x`.

## Inventario

| Subcarpeta | Propósito | Trigger |
|------------|-----------|---------|
| `pr_review/` | AI PR reviewer (Gemini/OpenAI) que comenta inline en cada PR | GitHub Actions `.github/workflows/ai-review.yml` |
