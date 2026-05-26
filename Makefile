# ZAFIRA-CORE — Makefile
# Uso: `make <comando>`. Lista todos los comandos con `make help`.

PYTHON ?= python
MANAGE ?= $(PYTHON) manage.py
PIP    ?= pip
HOST   ?= 0.0.0.0
PORT   ?= 8000

.DEFAULT_GOAL := help

# ── Help ──────────────────────────────────────────────────────────────
.PHONY: help
help: ## Muestra esta ayuda
	@echo ""
	@echo "  ZAFIRA-CORE — comandos disponibles:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# ── Setup inicial ─────────────────────────────────────────────────────
.PHONY: install
install: ## Instala dependencias (requirements/base.txt)
	$(PIP) install -r requirements/base.txt

.PHONY: install-dev
install-dev: ## Instala dependencias de desarrollo (requirements/dev.txt)
	$(PIP) install -r requirements/dev.txt

.PHONY: setup
setup: install migrate insert-data ## Setup completo (install + migrate + insert-data)
	@echo ""
	@echo "  ✅ Setup terminado. Usuario por defecto: admin / admin"
	@echo "  ▶  Inicia el servidor con: make run"

# ── Base de datos ─────────────────────────────────────────────────────
.PHONY: migrate
migrate: ## Aplica las migraciones pendientes
	$(MANAGE) migrate

.PHONY: makemigrations
makemigrations: ## Genera nuevas migraciones a partir de los modelos
	$(MANAGE) makemigrations

.PHONY: showmigrations
showmigrations: ## Lista el estado de todas las migraciones
	$(MANAGE) showmigrations

.PHONY: insert-data
insert-data: ## Carga datos iniciales (módulos + grupo Admin + usuario admin/admin)
	$(MANAGE) insert_data

.PHONY: superuser
superuser: ## Crea un superusuario interactivamente
	$(MANAGE) createsuperuser

.PHONY: dbshell
dbshell: ## Abre el shell de la base de datos
	$(MANAGE) dbshell

# ── Servidor / desarrollo ─────────────────────────────────────────────
.PHONY: run
run: ## Levanta el servidor de desarrollo en $(HOST):$(PORT)
	$(MANAGE) runserver $(HOST):$(PORT)

.PHONY: shell
shell: ## Abre el shell interactivo de Django
	$(MANAGE) shell

.PHONY: check
check: ## Ejecuta el system check de Django
	$(MANAGE) check

.PHONY: collectstatic
collectstatic: ## Recolecta archivos estáticos para producción
	$(MANAGE) collectstatic --noinput

# ── Tests / calidad ───────────────────────────────────────────────────
.PHONY: test
test: ## Ejecuta toda la suite de tests
	$(MANAGE) test app.common app.security app.auth app.profiles

.PHONY: test-app
test-app: ## Ejecuta tests de una app específica: `make test-app APP=auth`
	$(MANAGE) test app.$(APP)

.PHONY: test-fast
test-fast: ## Tests reutilizando la BD (más rápido en runs sucesivos)
	$(MANAGE) test app.common app.security app.auth app.profiles --keepdb

# ── Scraper ───────────────────────────────────────────────────────────
.PHONY: scrape
scrape: ## Ejecuta scraper de Moda RM (default: modarm, verbose)
	$(MANAGE) scrape --store modarm --verbose

.PHONY: scrape-quiet
scrape-quiet: ## Ejecuta scraper sin output detallado
	$(MANAGE) scrape --store modarm

# ── Mantenimiento ─────────────────────────────────────────────────────
.PHONY: clean
clean: ## Borra __pycache__ y archivos compilados
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@echo "  ✅ Caches limpiados"

.PHONY: kill-python
kill-python: ## Mata todos los procesos python (útil si la BD queda locked)
	@taskkill.exe //F //IM python.exe 2>/dev/null || pkill -9 python 2>/dev/null || true
	@echo "  ✅ Procesos python finalizados"

.PHONY: freeze
freeze: ## Vuelca las dependencias instaladas a requirements/_freeze.txt
	$(PIP) freeze > requirements/_freeze.txt
	@echo "  ✅ requirements/_freeze.txt actualizado"

.PHONY: reset-db
reset-db: ## ⚠ Borra db.sqlite3 y vuelve a migrar + insert-data
	@echo "  ⚠  Esto borrará TODOS los datos locales."
	@read -p "  ¿Continuar? [y/N] " ans && [ "$$ans" = "y" ] || exit 1
	rm -f db.sqlite3
	$(MAKE) migrate
	$(MAKE) insert-data
