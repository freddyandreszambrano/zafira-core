# ZAFIRA-CORE Makefile
# Uso: make <comando>. Lista comandos con: make help


# ⚙️ Variables base
PYTHON ?= python
MANAGE ?= $(PYTHON) manage.py
PIP ?= pip
HOST ?= 0.0.0.0
PORT ?= 8000
COMPOSE ?= docker compose -f deploy/docker-service-zafira/docker-compose.yml
DB_REDIS_COMPOSE ?= docker compose -f deploy/docker-service-zafira/docker-compose.db-redis.yml
SQLITE_DB ?= db.sqlite3
PRE_COMMIT_CONFIG ?= dev/pre-commit-config.yaml
env ?= develop

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
install-dev: ## Instala pip-tools y dependencias de desarrollo
	$(PIP) install pip-tools
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

.PHONY: compile
compile: ## Recompila los .txt bloqueados desde los .in (requiere pip-tools)
	pip-compile requirements/base.in -o requirements/base.txt --no-header --strip-extras
	pip-compile requirements/dev.in  -o requirements/dev.txt  --no-header --strip-extras
	pip-compile requirements/prod.in -o requirements/prod.txt --no-header --strip-extras
	@echo "  ✅ requirements/*.txt regenerados"

.PHONY: compile-upgrade
compile-upgrade: ## Recompila actualizando a las últimas versiones compatibles
	pip-compile --upgrade requirements/base.in -o requirements/base.txt --no-header --strip-extras
	pip-compile --upgrade requirements/dev.in  -o requirements/dev.txt  --no-header --strip-extras
	pip-compile --upgrade requirements/prod.in -o requirements/prod.txt --no-header --strip-extras
	@echo "  ✅ Dependencias actualizadas"

.PHONY: freeze
freeze: ## Vuelca dependencias instaladas (debug) a requirements/_freeze.txt
	$(PIP) freeze > requirements/_freeze.txt
	@echo "  ✅ requirements/_freeze.txt actualizado"


# 🔐 Utilidades
.PHONY: secret-key
secret-key: ## Genera un SECRET_KEY de Django
	@$(PYTHON) -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

start_project:
	if [ "$(environment)" == "local" ]; then \
		make run_command; \
	else \
		printf "Please, run the command in the local environment\n"; \
	fi


run_command:
	#make delete_migrations
	if [ "$(is_psql)" == "1" ]; then \
		make kill_session; \
		make delete_create_database; \
		make delete_create_schema; \
	fi
	make update_database
	if [ "$(is_initial)" == "1" ]; then \
		make insert-data; \
	fi
	if [ "$(is_reindex)" == "1" ]; then \
		make reindex_database; \
	fi
	if [ "$(is_backup)" == "1" ]; then \
		make load_backup file="data"; \
	fi

# 🐳 Docker

load_backup: # file="user"
	if [ "$(is_docker_monolith)" == "1" ]; then \
		docker exec -it $(project_name)-monolith python manage.py loaddata backup/$(file).json; \
	else \
		python manage.py loaddata backup/$(file).json; \
	fi


reindex_database:
	if [ "$(db_remote)" == "1" ]; then \
		psql -h $(db_host) -U $(db_user) -d $(db_name) -c "delete from $(db_schema).auth_permission; ALTER SEQUENCE $(db_schema).auth_permission_id_seq RESTART WITH 1; delete from $(db_schema).django_content_type; ALTER SEQUENCE $(db_schema).django_content_type_id_seq RESTART WITH 1;"; \
	elif [ "$(is_psql)" == "1" ]; then \
		docker exec $(postgres) psql -U $(db_user) -d $(db_name) -c "delete from $(db_schema).auth_permission; ALTER SEQUENCE $(db_schema).auth_permission_id_seq RESTART WITH 1; delete from $(db_schema).django_content_type; ALTER SEQUENCE $(db_schema).django_content_type_id_seq RESTART WITH 1;"; \
	else \
		sqlite3 db.sqlite3 "delete from auth_permission; delete from sqlite_sequence where name='auth_permission'; delete from django_content_type; delete from sqlite_sequence where name='django_content_type';"; \
	fi


delete_create_schema:
	if [ "$(is_docker_postgres)" == "1" ]; then \
  		docker exec -it $(postgres) psql -U $(db_user) -d $(db_name) -c "DROP SCHEMA IF EXISTS $(db_schema) CASCADE; CREATE SCHEMA $(db_schema);"; \
  	elif [ "$(db_remote)" == "1" ]; then \
  	    psql -h $(db_host) -p $(db_port) -U $(db_user) -d $(db_name) -c "DROP SCHEMA IF EXISTS $(db_schema) CASCADE; CREATE SCHEMA $(db_schema);"; \
  	else \
  	    psql -U $(db_user) -d $(db_name) -c "DROP SCHEMA IF EXISTS $(db_schema) CASCADE; CREATE SCHEMA $(db_schema);"; \
  	fi

delete_create_database:
	if [ "$(is_docker_postgres)" == "1" ]; then \
  		docker exec -it $(postgres) psql -U $(db_user) -d postgres -c "DROP DATABASE IF EXISTS $(db_name);" -c "CREATE DATABASE $(db_name);"; \
  	elif [ "$(db_remote)" == "1" ]; then \
  	    psql -h $(db_host) -p $(db_port) -U $(db_user) -d postgres -c "DROP DATABASE IF EXISTS $(db_name);" -c "CREATE DATABASE $(db_name)"; \
  	else \
  	    psql -U $(db_user) -d postgres -c "DROP DATABASE IF EXISTS $(db_name);" -c "CREATE DATABASE $(db_name)"; \
  	fi

kill_session:
	if [ "$(is_docker_postgres)" == "1" ]; then \
		docker exec $(postgres) psql -U $(db_user) -d $(db_name) -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE  pid <> pg_backend_pid() AND datname = '$(db_name)';"; \
	elif [ "$(db_remote)" == "1" ]; then \
		psql -h $(db_host) -p $(db_port) -U $(db_user) -d $(db_name) -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE  pid <> pg_backend_pid() AND datname = '$(db_name)';"; \
	else \
		psql -U $(db_user) -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE  pid <> pg_backend_pid() AND datname = '$(db_name)';"; \
	fi

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

# 🌿 Celery (local)
.PHONY: celery
celery: ## Inicia el worker de Celery + beat embebido (requiere Redis: make redis-local)
	$(PYTHON) -m celery -A core worker -B --concurrency=1 --loglevel=info

.PHONY: flower
flower: ## Inicia el panel Flower de Celery en http://localhost:5555
	$(PYTHON) -m celery -A core flower --port=5555

.PHONY: redis-local
redis-local: ## Levanta un Redis local en Docker como broker de Celery
	docker run --rm -p 6379:6379 --name zafira-redis redis:7-alpine


# 🧱 Postgres + Redis local (sin el app dockerizado)
.PHONY: db-redis-up
db-redis-up: ## Levanta Postgres + Redis en background (BD + broker de Celery)
	$(DB_REDIS_COMPOSE) up -d
	@echo "  ✅ Postgres en localhost:5432 · Redis en localhost:6379"
	@echo "  ▶  Django y Celery se corren en local: make run / make celery"

.PHONY: db-redis-down
db-redis-down: ## Detiene Postgres + Redis (conserva los datos)
	$(DB_REDIS_COMPOSE) down

.PHONY: db-redis-logs
db-redis-logs: ## Sigue los logs de Postgres + Redis
	$(DB_REDIS_COMPOSE) logs -f

.PHONY: db-redis-reset
db-redis-reset: ## ⚠️ Detiene Postgres + Redis y borra sus datos (volúmenes)
	$(DB_REDIS_COMPOSE) down -v


.PHONY: last_tag
last_tag: ## Lista las últimas tags por entorno: make last_tag env=develop|main
	@if [ "$(env)" != "develop" ] && [ "$(env)" != "main" ]; then \
		echo "env inválido: $(env). Usa env=develop o env=main"; \
		exit 1; \
	fi
	@echo "Últimas tags para $(env):"
	@git tag -l "$(env)-v*" --sort=-creatordate | head -n 3

.PHONY: tag
tag: last_tag ## Crea y pushea la siguiente tag por entorno: make tag env=develop|main
	@echo "Creando nuevo tag para entorno: $(env)"
	@remote_tag=$$(git ls-remote --tags origin "$(env)-v*" | sed -E "s#.*refs/tags/($(env)-v[0-9]+\.[0-9]+\.[0-9]+).*#\1#" | sort -V | tail -n 1); \
	local_tag=$$(git tag -l "$(env)-v*" | sort -V | tail -n 1); \
	if [ -n "$$local_tag" ] && [ "$$local_tag" != "$$remote_tag" ]; then \
		new_tag="$$local_tag"; \
	else \
		last_tag="$$remote_tag"; \
		if [ -z "$$last_tag" ]; then \
			last_tag="$$local_tag"; \
		fi; \
		if [ -z "$$last_tag" ]; then \
			new_tag="$(env)-v0.0.1"; \
		else \
			version=$$(echo $$last_tag | sed -E "s/$(env)-v//"); \
			major=$$(echo $$version | cut -d. -f1); \
			minor=$$(echo $$version | cut -d. -f2); \
			patch=$$(echo $$version | cut -d. -f3); \
			if [ "$$patch" -lt 99 ]; then \
				new_patch=$$(($$patch + 1)); \
			else \
				new_patch=0; \
				if [ "$$minor" -lt 99 ]; then \
					new_minor=$$(($$minor + 1)); \
				else \
					new_minor=0; \
					major=$$(($$major + 1)); \
				fi; \
				minor=$${new_minor:-$$minor}; \
			fi; \
			new_tag="$(env)-v$$major.$$minor.$$new_patch"; \
		fi; \
	fi; \
	echo "Nuevo tag: $$new_tag"; \
	printf "Presiona Enter para confirmar o Ctrl+C para cancelar..."; \
	read _confirm; \
	if git rev-parse "$$new_tag" >/dev/null 2>&1; then \
		echo "La tag $$new_tag ya existe localmente. Se intentará pushearla."; \
	else \
		git tag -a $$new_tag -m "version $$new_tag"; \
	fi; \
	git push origin $$new_tag
