# ZAFIRA-CORE Makefile
# Uso: make <comando>. Lista comandos con: make help


# ⚙️ Variables base
PYTHON ?= python
MANAGE ?= $(PYTHON) manage.py
PIP ?= pip
HOST ?= 0.0.0.0
PORT ?= 8000
COMPOSE ?= docker compose -f deploy/docker/docker-compose.yml
SQLITE_DB ?= db.sqlite3
PRE_COMMIT_CONFIG ?= dev/pre-commit-config.yaml

PROJECT_NAME := $(or $(shell sed -n 's/^PROJECT_NAME=//p' .env 2>/dev/null | tail -n 1),zafira)
DOCKER_MONOLITH := $(or $(shell sed -n 's/^DOCKER_MONOLITH=//p' .env 2>/dev/null | tail -n 1),0)

.DEFAULT_GOAL := help


# 🧭 Ayuda
.PHONY: help
help: ## Muestra esta ayuda
	@$(PYTHON) scripts/make_help.py $(MAKEFILE_LIST)


# 🚀 Setup inicial
.PHONY: install
install: ## Instala dependencias base
	$(PIP) install -r requirements/base.txt

.PHONY: install-dev
install-dev: ## Instala dependencias de desarrollo
	$(PIP) install -r requirements/dev.txt

.PHONY: setup
setup: install migrate insert-data ## Instala, migra y carga datos iniciales
	@echo ""
	@echo "  ✅ Setup terminado. Usuario por defecto: admin / admin"
	@echo "  ▶  Inicia el servidor con: make run"


# 🧑‍💻 Desarrollo Django
.PHONY: run
run: ## Levanta el servidor de desarrollo
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


# 🗄️ Base de datos
.PHONY: makemigrations
makemigrations: ## Genera nuevas migraciones desde los modelos
	$(MANAGE) makemigrations

.PHONY: migrate
migrate: ## Aplica migraciones pendientes
	$(MANAGE) migrate

.PHONY: showmigrations
showmigrations: ## Lista el estado de las migraciones
	$(MANAGE) showmigrations

.PHONY: update_database
update_database: ## Genera y aplica migraciones
	if [ "$(DOCKER_MONOLITH)" = "1" ]; then \
		docker exec -it $(PROJECT_NAME)-monolith python manage.py makemigrations; \
		docker exec -it $(PROJECT_NAME)-monolith python manage.py migrate; \
	else \
		$(MANAGE) makemigrations; \
		$(MANAGE) migrate; \
	fi

.PHONY: insert-data
insert-data: ## Carga módulos, grupo Administrador y admin/admin
	$(MANAGE) insert_data

.PHONY: reset-db
reset-db: ## ⚠️ Borra SQLite local, migra y carga datos iniciales
	@echo "  ⚠️  Esto borrará TODOS los datos locales."
	@read -p "  ¿Continuar? [y/N] " ans && [ "$$ans" = "y" ] || exit 1
	rm -f $(SQLITE_DB)
	$(MAKE) migrate
	$(MAKE) insert-data

.PHONY: dbshell
dbshell: ## Abre el shell de la base de datos
	$(MANAGE) dbshell

.PHONY: superuser
superuser: ## Crea un superusuario interactivamente
	$(MANAGE) createsuperuser


# ✅ Tests
.PHONY: test
test: ## Ejecuta toda la suite de tests
	$(MANAGE) test core.common core.security core.auth core.profiles

.PHONY: test-app
test-app: ## Ejecuta tests de una app: make test-app APP=auth
	$(MANAGE) test core.$(APP)

.PHONY: test-fast
test-fast: ## Ejecuta tests reutilizando la BD
	$(MANAGE) test core.common core.security core.auth core.profiles --keepdb


# 🧹 Calidad de código
.PHONY: format
format: ## Formatea con black e isort
	black core/ config/
	isort core/ config/

.PHONY: format-check
format-check: ## Verifica formato sin modificar archivos
	black --check core/ config/
	isort --check-only core/ config/

.PHONY: lint
lint: ## Corre flake8 sobre core y config
	flake8 core/ config/ --max-line-length=100 --extend-ignore=E203,W503

.PHONY: pre-commit-install
pre-commit-install: ## Instala hooks de pre-commit
	$(PIP) install pre-commit
	pre-commit --config $(PRE_COMMIT_CONFIG) install
	@echo "  ✅ Hooks instalados"

.PHONY: pre-commit-run
pre-commit-run: ## Corre todos los hooks de pre-commit
	pre-commit --config $(PRE_COMMIT_CONFIG) run --all-files


# 🕷️ Scraper
.PHONY: scrape
scrape: ## Ejecuta scraper de Moda RM con salida detallada
	$(MANAGE) scrape --store modarm --verbose

.PHONY: scrape-quiet
scrape-quiet: ## Ejecuta scraper de Moda RM sin salida detallada
	$(MANAGE) scrape --store modarm


# 🧰 Mantenimiento
.PHONY: clean
clean: ## Borra __pycache__ y archivos Python compilados
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@echo "  ✅ Caches limpiados"

.PHONY: kill-python
kill-python: ## Mata procesos Python que puedan bloquear SQLite
	@taskkill.exe //F //IM python.exe 2>/dev/null || pkill -9 python 2>/dev/null || true
	@echo "  ✅ Procesos python finalizados"

.PHONY: freeze
freeze: ## Vuelca dependencias instaladas a requirements/_freeze.txt
	$(PIP) freeze > requirements/_freeze.txt
	@echo "  ✅ requirements/_freeze.txt actualizado"


# 🔐 Utilidades
.PHONY: secret-key
secret-key: ## Genera un SECRET_KEY de Django
	@$(PYTHON) -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"


# 🐳 Docker
.PHONY: docker-build
docker-build: ## Construye la imagen Docker
	$(COMPOSE) build

.PHONY: docker-up
docker-up: ## Levanta stack Docker en background
	$(COMPOSE) up -d --build
	@echo "  ✅ Stack arriba en http://localhost:8000 (admin/admin)"

.PHONY: docker-down
docker-down: ## Baja el stack Docker conservando volúmenes
	$(COMPOSE) down

.PHONY: docker-logs
docker-logs: ## Sigue logs del servicio web
	$(COMPOSE) logs -f web

.PHONY: docker-shell
docker-shell: ## Abre bash dentro del servicio web
	$(COMPOSE) exec web bash

.PHONY: docker-clean
docker-clean: ## ⚠️ Baja stack Docker y borra volúmenes
	$(COMPOSE) down -v
