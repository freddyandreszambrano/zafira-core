---
name: Django Patterns & Conventions
description: Development patterns, coding conventions, and best practices for ZAFIRA
type: feedback
---

# Django Patterns & Conventions for ZAFIRA

## Code Organization Pattern

**Rule**: Use `__init__.py` to export public API from each package.

**How to apply**: When adding new forms/views/utils, always export them via __init__.py so consumers can do:
```python
from app.auth.forms import LoginForm  # ✓ Clean import
```
Instead of:
```python
from app.auth.forms.forms import LoginForm  # ✗ Verbose import
```

**Why**: Keeps imports short, hides internal structure, makes refactoring easier.

---

## View Organization Pattern

**Rule**: Web views (HTML-rendering) and API views (JSON) should be explicitly separated.

**How to apply**:
- Web views: Named `*View` (LoginView, DashboardView)
- API views: Named `*AjaxView` or `*APIView` (ListUsersAjaxView)
- URL routes grouped by type: `web_urls = [...]` and `ajax_urls = [...]`

**Why**: Clear intent, prevents accidentally returning JSON from HTML routes or vice versa.

---

## Form Usage Pattern

**Rule**: Always validate form input before processing, even for AJAX.

**How to apply**:
```python
form = EditUserForm(request.POST, instance=user)
if form.is_valid():
    form.save()
    return JsonResponse({'success': True})
else:
    return JsonResponse({'errors': form.errors}, status=400)
```

**Why**: Prevents invalid data in database, provides meaningful error messages.

---

## Permission Checking Pattern

**Rule**: Check permissions explicitly at view method level.

**How to apply**:
```python
class AdminAjaxView(LoginRequiredMixin, View):
    def post(self, request):
        if not request.user.is_staff:  # ← Explicit check
            return JsonResponse({'error': 'Denied'}, status=403)
```

Use `LoginRequiredMixin` for login requirement, then check specific permissions.

**Why**: Clearer than custom mixins, easier to debug, standard Django pattern.

---

## Requirements Management

**Rule**: Always separate base, dev, and prod dependencies.

**How to apply**:
- `requirements/base.txt`: Core dependencies (Django, DRF, etc.)
- `requirements/dev.txt`: -r base.txt + dev tools (pytest, black, etc.)
- `requirements/prod.txt`: -r base.txt + production packages (gunicorn, psycopg2, etc.)

For deployment:
```bash
pip install -r requirements/prod.txt
```

For development:
```bash
pip install -r requirements/dev.txt
```

**Why**: Keeps production deployments light, dev environments get helpful tools, avoids unnecessary dependencies.

---

## Template Block Pattern

**Rule**: Use named blocks in base.html for extensibility.

**How to apply**:
```html
<!-- base.html -->
{% block title %}ZAFIRA{% endblock %}
{% block content %}{% endblock %}
{% block extra_js %}{% endblock %}

<!-- child template -->
{% extends "base.html" %}
{% block title %}Login - ZAFIRA{% endblock %}
{% block content %}<form>...</form>{% endblock %}
```

**Why**: DRY principle, consistent styling, easy layout changes.

---

## AJAX Pattern

**Rule**: Always include CSRF token in AJAX POST requests.

**How to apply**:
```javascript
const formData = new FormData();
formData.append('user_id', userId);
formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

fetch('/api/users/delete/', {method: 'POST', body: formData})
```

**Why**: Django's CSRF protection requires it, prevents CSRF attacks.

---

## Model Method Pattern

**Rule**: Put business logic in model methods, not views.

**How to apply**:
```python
# In model
def get_full_name(self):
    return f"{self.first_name} {self.last_name}".strip()

# In template
{{ user.get_full_name }}

# NOT in view
full_name = f"{user.first_name} {user.last_name}"
```

**Why**: Single source of truth, reusable across views and templates, easier to test.

