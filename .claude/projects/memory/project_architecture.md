---
name: ZAFIRA Project Architecture
description: Overall architecture, patterns, and design decisions for ZAFIRA admin system
type: project
---

# ZAFIRA - Project Architecture & Design

## Overview
ZAFIRA is a Django-based administrative dashboard system with user management, authentication, and role-based access control.

## Technology Stack
- **Backend**: Django 5.2.14
- **API**: Django REST Framework
- **Frontend**: HTML/CSS (Tailwind), JavaScript (AJAX)
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Auth**: Django's built-in auth + custom User model

## Architecture Decisions

### 1. Custom User Model
- Extends `AbstractBaseUser` and `PermissionsMixin`
- Fields: username, email, dni (ID), first_name, last_name, image
- Tracks last_password_change_at for security
- force_password_change flag for forcing password resets

### 2. Modular App Structure
```
auth/
  ├── forms/     → Form classes (isolated, clean imports)
  ├── views/     → CBV and AJAX endpoints
  ├── utils/     → Utility functions for email, validation
  ├── models.py  → Data models
  └── urls.py    → URL routing
```

**Why**: Prevents massive imports, makes components reusable, easier to test.

### 3. Separate Web & API URLs
- **Web routes**: HTML-rendering views (/auth/login, /dashboard, /users)
- **AJAX API**: JSON endpoints for dynamic functionality (/api/users/list, /api/users/edit)

### 4. Class-Based Views (CBV)
All views use Django's CBV pattern:
- Mixins: `LoginRequiredMixin`, `UserPassesTestMixin`
- Generic views: `TemplateView`, `UpdateView`
- Custom views: `View` for AJAX endpoints

### 5. Form Validation
- `LoginForm`: Authenticates user, prevents invalid logins
- `EditUserForm`: Admin form for updating user data
- `ChangePasswordForm`: Requires old password verification
- `ResetPasswordForm`: Admin password reset without verification

## Data Flow

### Login Flow
1. User submits LoginForm
2. Form authenticates via Django's `authenticate()`
3. Session created via `login()`
4. Redirect to dashboard

### User Management (AJAX)
1. Frontend fetch() → /api/users/list/
2. Backend returns JSON with paginated users
3. Frontend renders table dynamically
4. User clicks Edit/Delete → another AJAX request
5. Backend updates/deletes and returns JSON response

### Password Reset (Admin)
1. Admin accesses users list
2. Clicks "Reset Password" on user row
3. Modal form with new password
4. POST to /api/users/reset-password/
5. Backend changes password, returns success

## Security Considerations

✓ **Implemented**:
- CSRF protection on forms
- Password hashing with Django's built-in methods
- Permission checks (is_staff) on admin views
- Session-based authentication for web
- JWT tokens available for API (via REST framework)

⚠️ **For Production**:
- Enable SECURE_SSL_REDIRECT
- Use HTTPS only
- Set strong SECRET_KEY
- Configure ALLOWED_HOSTS
- Use PostgreSQL instead of SQLite
- Enable Django security middleware

## Future Extensibility

The structure allows easy addition of:
- New forms: Add to `forms/forms.py` and export via `__init__.py`
- New views: Add to `views/views.py` (web) or new AJAX view
- New utilities: Add to `utils/helpers.py`
- New models: Add to `models.py` and create migrations

All without touching existing code.
