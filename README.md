# ZAFIRA-CORE - Sistema de Autenticación Corporativo Django

[![Django](https://img.shields.io/badge/Django-5.2.14-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14.0-blue.svg)](https://www.django-rest-framework.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-yellow.svg)](https://www.python.org/)

Sistema completo de **autenticación corporativa** con **permisos**, **grupos**, **perfiles extendidos** y **API REST**.

---

## ⚡ Setup Rápido (30 segundos)

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar setup automático
python quick_setup.py

# 3. Crear superusuario
python manage.py createsuperuser

# 4. Iniciar servidor
python manage.py runserver
```

✅ **Listo en http://localhost:8000/admin/**

---

## 📦 ¿Qué Incluye?

### **2 Aplicaciones Django**

#### 🔐 **App AUTH** - Autenticación y Permisos
- ✅ User model personalizado con campos corporativos
- ✅ Login/Registro con validación completa
- ✅ Token + JWT authentication dual
- ✅ Reset de contraseña por email
- ✅ Gestión de permisos y grupos
- ✅ Admin panel completo
- ✅ 7 endpoints REST principales

#### 👤 **App PROFILES** - Datos Corporativos
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
GET    /api/profiles/me/                        → Mi perfil
PUT    /api/profiles/me_update/                 → Actualizar mi perfil
GET    /api/profiles/                           → Listar todos los perfiles
GET    /api/profiles/{id}/                      → Obtener perfil
PUT    /api/profiles/{id}/                      → Actualizar perfil
DELETE /api/profiles/{id}/                      → Eliminar perfil
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

**Por defecto usa base de datos en memoria** (sin problemas WSL/SQLite).

### Cambiar a archivo SQLite
En `config/settings.py`:
```python
'NAME': BASE_DIR / 'var' / 'db' / 'db.sqlite3',  # SQLite local persistente
```

### Usar PostgreSQL (Producción)
```bash
pip install psycopg2-binary
```

En `config/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'zafira',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Ver: `DATABASE_SETUP.md` para más opciones.

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
├── var/                         # Runtime local ignorado por git
│   └── db/db.sqlite3            # Base SQLite local
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

- **`SETUP_GUIDE.md`** - Guía completa de instalación
- **`DATABASE_SETUP.md`** - Configuración de bases de datos
- **`docs/DESIGN_SYSTEM.md`** - 🎨 Sistema de diseño ZAFIRA (colores, utilities Tailwind, patrones de componentes)
- **`docs/stich/DESIGN.md`** - Guías completas de marca (tipografía, layout, UX)
- **`quick_setup.py`** - Script de setup automático
- **`setup_db.py`** - Setup manual alternativo

### 🎨 Colores de Marca ZAFIRA (Quick Reference)

| Token Tailwind | Hex | Uso |
|---|---|---|
| `zafira-primary` | `#FF3BBE` | Cyber-Magenta - Acciones principales |
| `zafira-secondary` | `#8E54FF` | Electric-Violet - Acciones secundarias |
| `zafira-obsidian` | `#090101` | Obsidian - Fondos oscuros, sombras |
| `zafira-slate` | `#94A3BB` | Cool Slate - Texto secundario, bordes |

Ver `docs/DESIGN_SYSTEM.md` para la paleta completa y patrones de uso.

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
**Solución:** Usar base de datos en memoria (por defecto) o PostgreSQL.

### "No module named 'django'"
```bash
pip install -r requirements.txt
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
1. Revisa `SETUP_GUIDE.md` y `DATABASE_SETUP.md`
2. Verifica los logs: `python manage.py runserver`
3. Usa Django shell: `python manage.py shell`

---

## 📞 ¡Listo para Usar!

```bash
python quick_setup.py
python manage.py createsuperuser
python manage.py runserver
```

**¡Accede a http://localhost:8000/admin/ y comienza a usar tu sistema de autenticación corporativo!** 🚀
