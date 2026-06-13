# ZAFIRA-CORE Copilot Instructions

When reviewing pull requests, respond in Spanish and prioritize bugs, security regressions, permission leaks, broken Django behavior, and missing tests.

Project context:
- ZAFIRA-CORE is a Django 5.2 administrative dashboard.
- The menu and permissions are database-driven through the `security` app.
- Stack: Django, DRF, SQLite in development, PostgreSQL in production, Tailwind CDN, DataTables, FormValidation, `django-crum`, and `django-widget-tweaks`.

Review rules:
- CRUD modules must use four explicit views: `ListView`, `CreateView`, `UpdateView`, and `DeleteView`.
- Do not recommend generic CRUD base classes or AJAX-only views.
- Every CRUD view must inherit `PermissionMixin` and define `permission_required`.
- `PermissionMixin.dispatch()` owns permission checks. CRUD `post()` methods should not duplicate group permission validation.
- Public auth views should use `PublicMixin`.
- List/Create/Update/Delete actions should be handled inline in each view `post()` with clear `if/elif` branches.
- Common POST actions are `search`, `change_state`, `add`, `edit`, and `validate_data`.
- Models used by DataTables list endpoints should expose `to_json()`.
- Prefer `Choice.get_label(value)` or `obj.get_field_display()` over `dict(MODEL_CHOICES)`.
- Use `TextChoicesCustom` from `core.common.choices` for enums.
- Use `FORM_INPUT_CLASS` and widget factories from `core.common.forms.widgets` for form inputs.

Template and static rules:
- Entity templates live inside the app: `core/<app>/templates/<entity>/`.
- Entity JavaScript lives inside the app: `core/<app>/static/<entity>/js/`.
- Root `templates/` is only for shared bases: `base.html`, `base_public.html`, `list.html`, `form.html`, and `delete.html`.
- Do not add inline JavaScript to templates.
- Avoid empty pass-through templates. If a template only extends a base without adding content, point `template_name` directly to the base.

Code quality:
- Keep imports at the top of files.
- Split files that grow past roughly 200 lines or contain more than five classes.
- Avoid obvious docstrings and comments.
- Keep changes scoped to the requested behavior.
- Add or update focused tests when behavior, permissions, validation, or user-facing flows change.
