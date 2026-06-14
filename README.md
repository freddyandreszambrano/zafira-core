# ZAFIRA-CORE - Sistema de Autenticación Corporativo Django

[![Django](https://img.shields.io/badge/Django-5.2.14-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14.0-blue.svg)](https://www.django-rest-framework.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-yellow.svg)](https://www.python.org/)

Sistema completo de **autenticación corporativa** con **permisos**, **grupos**, **perfiles extendidos** y **API REST**.

---

## ⚡ Setup Rápido

```bash
# 1. Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate   # Linux / Mac
.venv\Scripts\activate      # Windows

# 2. Instalar dependencias de desarrollo
pip install pip-tools
pip install -r requirements/dev.txt

# 3. Migrar y cargar datos iniciales
make migrate
make insert-data

# 4. Iniciar servidor
make run
```

O con el comando combinado:

```bash
make install-dev && make setup && make run
```

Usuario inicial: `admin / admin`. Listo en `http://localhost:8000/`.

---

## 📦 ¿Qué Incluye?

### **Apps Django principales**

#### 🔐 **Security + Auth** - Módulos, permisos y usuarios
- ✅ User model personalizado con campos corporativos
- ✅ Login/Registro con validación completa
- ✅ Token + JWT authentication dual
- ✅ Reset de contraseña por email
- ✅ Gestión de permisos y grupos
- ✅ Admin panel completo
- ✅ 7 endpoints REST principales

#### 👤 **Profiles** - Datos corporativos
- ✅ Perfil extendido de usuario
- ✅ Departamentos, cargos, teléfono
- ✅ Relaciones jerárquicas (manager)
- ✅ Estado de verificación
- ✅ Auto-crear perfil con usuario
- ✅ 4 endpoints REST

### **Configuración Django**
- ✅ DRF completo
- ✅ CORS habilitado
- ✅ Email backend
- ✅ JWT tokens
- ✅ Media files
- ✅ Señales automáticas

---

## 🚀 API Endpoints

### Autenticación
```
POST   /api/auth/users/                         → Registrar usuario
POST   /api/auth/login/                         → Login (Token + JWT)
POST   /api/auth/logout/                        → Logout
GET    /api/auth/users/me/                      → Obtener usuario actual
PUT    /api/auth/users/{id}/                    → Actualizar usuario
DELETE /api/auth/users/{id}/                    → Eliminar usuario
POST   /api/auth/users/change_password/         → Cambiar contraseña
POST   /api/auth/users/reset_password/          → Solicitar reset por email
POST   /api/auth/users/reset_password_confirm/  → Confirmar reset
```

### Perfiles
```
```

---

## 📋 Ejemplos de Uso

### Registrar Usuario
```bash
curl -X POST http://localhost:8000/api/auth/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "dni": "1234567890",
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePassword123!",
    "password2": "SecurePassword123!"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "SecurePassword123!"
  }'
```

Respuesta:
```json
{
  "token": "Token abc123def456...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {...}
}
```

### Usar Token en Requests
```bash
curl -H "Authorization: Token abc123def456..." \
  http://localhost:8000/api/auth/users/me/
```

---

## 🔐 Autenticación

**Dos métodos disponibles:**

### 1️⃣ Token Authentication (REST Framework)
```bash
Authorization: Token abc123def456...
```

### 2️⃣ JWT Authentication (SimpleJWT)
```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

Refrescar JWT:
```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"eyJ0eXAiOiJKV1QiLCJhbGc..."}'
```

---

## 👥 Grupos y Permisos

**3 grupos creados automáticamente:**

| Grupo | Permisos |
|-------|----------|
| **Admin** | Acceso completo a usuarios, grupos, permisos |
| **Manager** | Ver y crear usuarios, ver grupos |
| **User** | Ver información de usuarios |

Asignar grupo a usuario:
```python
from django.contrib.auth.models import Group
from core.auth.models import User

user = User.objects.get(username='john')
group = Group.objects.get(name='Manager')
user.groups.add(group)
```

---

## 📊 Modelos de Datos

### User Model
```python
- id (BigAutoField)
- username (CharField, unique)
- email (EmailField, unique)
- dni (CharField, unique) - Número de cédula
- first_name, last_name
- image (ImageField, optional)
- is_active, is_staff, is_superuser
- date_joined, last_login
- last_password_change_at
- force_password_change
- email_reset_token
- groups (M2M to Group)
- user_permissions (M2M to Permission)
```

### UserProfile Model
```python
- user (OneToOne to User)
- phone, address, city, country
- department (HR, IT, FINANCE, SALES, MARKETING, OPERATIONS)
- job_title
- manager (FK to User - optional)
- employee_id (unique)
- hire_date
- bio
- social_media (JSON string)
- is_verified
- created_at, updated_at
```

---

## 🗄️ Base de Datos

**Por defecto usa SQLite local** en `db.sqlite3`.

### Cambiar entre SQLite y PostgreSQL
En `.env`:
```env
PSQL=0  # SQLite local
PSQL=1  # PostgreSQL con DB_*
```

### Usar PostgreSQL

En `.env`:

```env
PSQL=1
DB_NAME=zafira
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_SCHEMA=public
```

La selección de motor vive en `config/db.py` y `config/settings.py`.

---

## 📧 Email Configuration

### Desarrollo (Console Backend)
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
Los emails se imprimen en la consola.

### Producción (Gmail SMTP)
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-app-password'
```

---

## 🛠️ Admin Panel

Accede a: **http://localhost:8000/admin/**

### Características
- ✅ Crear, editar, eliminar usuarios
- ✅ Asignar grupos y permisos
- ✅ Activar/desactivar cuentas
- ✅ Marcar para cambio obligatorio de contraseña
- ✅ Ver historial de login
- ✅ Gestionar perfiles
- ✅ Búsqueda y filtrado avanzado

---

## 📁 Estructura de Archivos

```
ZAFIRA-CORE/
├── ai/                          # Gobernanza, contexto y workflows para agentes IA
├── core/                        # Apps Django del dominio
│   ├── auth/                    # Autenticación, dashboard, perfil y usuarios
│   ├── common/                  # Utilidades compartidas
│   ├── profiles/                # Datos extendidos del usuario
│   ├── scraper/                 # Herramientas de extracción
│   └── security/                # Módulos, grupos y permisos dinámicos
├── config/                      # Settings, URLs y WSGI/ASGI
├── deploy/
│   └── docker/                  # Dockerfile y Compose
├── docs/                        # Documentación técnica
├── requirements/                # Dependencias por entorno
├── scripts/                     # Automatizaciones locales
├── static/                      # Assets globales
├── templates/                   # Bases compartidos
├── db.sqlite3                   # Base SQLite local ignorada por git
└── manage.py                    # Entrada CLI de Django
```

---

## 🔧 Comandos Útiles

```bash
# Crear superusuario
python manage.py createsuperuser

# Ejecutar migraciones
python manage.py migrate

# Crear grupos (manual)
python manage.py init_groups

# Servidor de desarrollo
python manage.py runserver

# Shell interactivo
python manage.py shell

# Ver usuarios
python manage.py shell
>>> from core.auth.models import User
>>> User.objects.all()

# Tests
python manage.py test

# Mostrar migraciones
python manage.py showmigrations
```

---

## 📚 Documentación Adicional

- **`AGENTS.md`** - Gobernanza obligatoria del proyecto
- **`docs/architecture.md`** - Estructura del repositorio y ubicación de archivos
- **`docs/development.md`** - Patrones de desarrollo, CRUD, permisos y comandos
- **`docs/design-system.md`** - Sistema de diseño ZAFIRA
- **`docs/project/root-files.md`** - Mapa de archivos raíz y por qué existen
- **`docs/project/changelog.md`** - Historial de cambios

### 🎨 Colores de Marca ZAFIRA (Quick Reference)

| Token Tailwind | Hex | Uso |
|---|---|---|
| `zafira-primary` | `#FF3BBE` | Cyber-Magenta - Acciones principales |
| `zafira-secondary` | `#8E54FF` | Electric-Violet - Acciones secundarias |
| `zafira-obsidian` | `#090101` | Obsidian - Fondos oscuros, sombras |
| `zafira-slate` | `#94A3BB` | Cool Slate - Texto secundario, bordes |

Ver `docs/design-system.md` para la paleta completa y patrones de uso.

---

## 📦 Gestión de dependencias (pip-tools)

El proyecto usa **pip-tools** para separar dependencias directas de transitivas:

| Archivo | Propósito |
|---|---|
| `requirements/base.in` | Dependencias directas compartidas (editar aquí) |
| `requirements/dev.in` | Dependencias directas de desarrollo (editar aquí) |
| `requirements/prod.in` | Dependencias directas de producción (editar aquí) |
| `requirements/base.txt` | Lock file generado — **no editar a mano** |
| `requirements/dev.txt` | Lock file generado — **no editar a mano** |
| `requirements/prod.txt` | Lock file generado — **no editar a mano** |

### Agregar una nueva dependencia

```bash
# 1. Editar el .in correspondiente
echo "nueva-libreria==1.2.3" >> requirements/base.in   # o dev.in / prod.in

# 2. Recompilar los lock files
make compile

# 3. Instalar
pip install -r requirements/dev.txt
```

### Actualizar todas las dependencias

```bash
make compile-upgrade
pip install -r requirements/dev.txt
```

### Instalación para producción

```bash
pip install -r requirements/prod.txt
```

---

## 🚀 Deployment (Producción)

### Checklist
- [ ] Cambiar `DEBUG = False` en settings.py
- [ ] Usar variables de entorno para secretos (use `.env`)
- [ ] Cambiar a PostgreSQL
- [ ] Configurar email SMTP
- [ ] Habilitar HTTPS (`SECURE_SSL_REDIRECT = True`)
- [ ] Configurar ALLOWED_HOSTS
- [ ] Ejecutar `collectstatic`
- [ ] Usar gunicorn o similar

### Comando Deploy
```bash
# Preparar para producción
python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Iniciar con gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

---

## 🐛 Troubleshooting

### "database is locked"
**Solución:** cerrar procesos que tengan abierto `db.sqlite3` o ejecutar:

```bash
make kill-python
```

### "No module named 'django'"
```bash
pip install -r requirements/base.txt
```

### "Table does not exist"
```bash
python manage.py migrate
```

### "Permission denied"
Asegúrate de que el usuario tiene los permisos correctos:
```python
from django.contrib.auth.models import Group
user.groups.add(Group.objects.get(name='Admin'))
```

---

## 📝 Licencia

MIT License - Libre para uso comercial y personal.

---

## 🎯 Características Incluidas

| Característica | Estado |
|---|---|
| User model personalizado | ✅ |
| Token Authentication | ✅ |
| JWT Authentication | ✅ |
| Password reset por email | ✅ |
| Gestión de grupos | ✅ |
| Gestión de permisos | ✅ |
| Perfil corporativo extendido | ✅ |
| Admin panel completo | ✅ |
| REST API completa | ✅ |
| CORS habilitado | ✅ |
| Validación de datos | ✅ |
| Tests listos | ✅ |

---

## 🤝 Soporte

Para preguntas o problemas:
1. Revisa `AGENTS.md` y `docs/`
2. Verifica los logs: `python manage.py runserver`
3. Usa Django shell: `python manage.py shell`

---

## 📞 ¡Listo para Usar!

```bash
make setup
make run
```

Accede a `http://localhost:8000/` con `admin / admin`.
