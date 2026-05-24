# ZAFIRA Project Memory Index

This file indexes all persistent memories about the ZAFIRA project.

## Project Documentation

- [Project Architecture](project_architecture.md) — Overall system design, technology stack, and architectural decisions
- [Django Patterns](django_patterns.md) — Coding conventions, patterns, and best practices used in this project

## Key Decisions

**Date**: 2026-05-17

- Implemented modular Django structure with `__init__.py` exports to avoid large imports
- Created class-based views for both web (HTML) and AJAX (JSON) endpoints
- Separated requirements.txt into base/dev/prod for better dependency management
- Used Tailwind CSS for responsive UI styling
- Custom User model extending AbstractBaseUser for flexible authentication

## Current Implementation Status

✅ **Completed**:
- Custom User model with DNI, email verification, password tracking
- Login/Logout views and forms
- Admin dashboard with statistics cards
- Users list management interface
- AJAX endpoints for user CRUD operations
- Password change/reset functionality
- Role-based access control (is_staff, is_active)

🚀 **Production Ready Features**:
- Form validation for all user inputs
- CSRF protection on forms
- Permission checking (LoginRequiredMixin, is_staff checks)
- Paginated user listings
- Search functionality for users
- Error handling and user feedback via JsonResponse

⏳ **Future Enhancements**:
- User groups and permissions system
- Advanced filtering/sorting on user list
- Audit logging for admin actions
- Two-factor authentication
- Email notifications for password resets
- User activity dashboard
- Role templates for quick user provisioning

## Quick Reference

**Template Base Path**: `templates/`
- Login: `templates/shared/auth/login.html`
- Dashboard: `templates/shared/dashboard/home.html`
- Users: `templates/shared/users/list.html`

**App Structure**:
```
app/auth/
  forms/__init__.py  → LoginForm, EditUserForm, ChangePasswordForm, ResetPasswordForm
  views/__init__.py  → LoginView, DashboardView, ListUsersAjaxView, etc.
  utils/__init__.py  → send_password_reset_email, validate_password_strength, etc.
  models.py          → Custom User model
  urls.py            → Web + AJAX URL routes
```

**URL Patterns**:
- `/auth/login/` — Login page
- `/dashboard/` — Admin dashboard
- `/users/` — User management interface
- `/api/users/list/` — AJAX: Get paginated user list
- `/api/users/edit/` — AJAX: Update user
- `/api/users/delete/` — AJAX: Delete user
- `/api/users/change-password/` — AJAX: Change user password

**Dependencies Management**:
```bash
pip install -r requirements/dev.txt    # Development
pip install -r requirements/prod.txt   # Production
```

## Notes

- The project uses Django 5.2.14 with Django REST Framework for API support
- Database defaults to SQLite for dev, recommended PostgreSQL for prod
- Static files served by Whitenoise in production
- CORS headers configured for frontend/backend separation
- JWT tokens available via djangorestframework-simplejwt
