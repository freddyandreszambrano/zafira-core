# pr_review/

AI-powered Pull Request reviewer. Comenta inline en archivos cambiados de un PR de GitHub usando un LLM (Gemini, OpenAI, o cualquier API compatible OpenAI).

Inspirado en `scripts/mr_review/reviewer.py` de `hey-support` (GitLab MR reviewer, 423 líneas), adaptado a GitHub PR API.

## Requisitos

- Python 3.11+ (stdlib only, sin `pip install`).
- GitHub token con permiso `pull-requests: write` (lo provee GitHub Actions vía `GITHUB_TOKEN`).
- Una key de provider AI (Gemini, OpenAI, o compatible).

## Variables de entorno

| Var | Obligatorio | Descripción |
|-----|-------------|-------------|
| `GITHUB_TOKEN` | sí | Token con permiso `pull-requests: write`. |
| `GITHUB_REPOSITORY` | sí | `owner/repo` (GitHub Actions lo expone). |
| `PR_NUMBER` | sí | Número del PR. |
| `AI_PROVIDER` | sí | `gemini` \| `openai` \| `custom`. |
| `AI_API_KEY` | sí | Key del provider. |
| `AI_MODEL` | no | Default por provider (`gemini-1.5-flash`, `gpt-4o-mini`). |
| `AI_BASE_URL` | solo `custom` | Endpoint OpenAI-compatible (OpenRouter, Ollama, etc.). |
| `MAX_DIFF_CHARS` | no | Trunca diff si excede. Default `40000`. |

## Uso local

```bash
export GITHUB_TOKEN=ghp_xxx
export GITHUB_REPOSITORY=FreddyAndres/ZAFIRA-CORE
export PR_NUMBER=42
export AI_PROVIDER=gemini
export AI_API_KEY=AIza...
python scripts/pr_review/reviewer.py
```

## Uso en CI

Ver `.github/workflows/ai-review.yml`. Se dispara en `pull_request` events.
Para evitar reviews duplicados en el mismo commit, el script deja un marker comment con el `head_sha` y skipea si ya existe.

## Severidades

Cada comentario lleva prefijo:

- 🔴 **critical** — bug, security, broken contract.
- 🟡 **improvement** — mejora notable, performance, claridad.
- 🟢 **suggestion** — nice-to-have, estilo.

## Setup en el repo

1. Generar API key del provider (https://aistudio.google.com/ para Gemini, https://platform.openai.com/ para OpenAI).
2. En GitHub repo → Settings → Secrets and variables → Actions → New secret:
   - `AI_API_KEY` = la key
3. Push a `develop`. Abrir un PR. El bot comentará en 30-60s.
