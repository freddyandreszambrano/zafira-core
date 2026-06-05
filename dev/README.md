# Desarrollo

Esta carpeta agrupa configuración de herramientas de desarrollo que no necesita vivir en la raíz para funcionar.

## Archivos

| Archivo | Uso |
|---|---|
| `pre-commit-config.yaml` | Hooks de pre-commit usados desde `make pre-commit-install` y `make pre-commit-run` |

## Archivos que se quedan en raíz

Algunos archivos no se mueven porque sus herramientas los descubren automáticamente solo en la raíz o en carpetas padre:

| Archivo | Motivo |
|---|---|
| `.editorconfig` | Auto-detectado por editores para formato e indentación |
| `.gitattributes` | Auto-detectado por Git para saltos de línea y binarios |
| `pyproject.toml` | Auto-detectado por black, isort, ruff, pytest, coverage y tooling Python |

`.python-version` queda como configuración local opcional de pyenv y está ignorado por Git.
