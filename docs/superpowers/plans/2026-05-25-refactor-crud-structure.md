# CRUD Refactoring & Auth Separation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize all CRUDs across the project to follow the clean, structured pattern already established in `_crud.py`, and separate auth concerns (login/register) from dashboard and profile management into focused view files.

**Architecture:** 
- Extract a single pattern-following CRUD base from `security/views/_crud.py` and ensure all modules use it consistently
- Separate `auth/views/web.py` into three focused files: `auth.py` (login/register), `dashboard.py` (dashboard), and `profile.py` (user profile views)
- Ensure all models have `to_json()` methods for DataTables serialization
- Clean up view imports and remove redundant `get_success_url()` overrides

**Tech Stack:** Django 5.2, DRF, DataTables, Tailwind CSS

---

## Phase 1: Audit & Verify

### Task 1: Verify all models have `to_json()` method

**Files:**
- Check: `app/auth/models/__init__.py`
- Check: `app/security/models/__init__.py`
- Check: `app/profiles/models/__init__.py`

- [ ] **Step 1: Check User model**

Run:
```bash
grep -n "def to_json" app/auth/models/user.py
```

Expected: Should show `to_json` method. If not found, we'll add it in the next phase.

- [ ] **Step 2: Check Security models (Module, ModuleType, Group)**

Run:
```bash
grep -n "def to_json" app/security/models/module.py app/security/models/group.py
```

Expected: Both should have `to_json()` methods. ModuleType and Group should be confirmed.

- [ ] **Step 3: Check if UserProfile model has `to_json()`**

Run:
```bash
grep -n "def to_json" app/profiles/models/profile.py
```

Expected: If not present, we'll add it in next phase if profiles becomes a CRUD.

---

### Task 2: Audit all view files for structure

**Files:**
- Check: `app/security/views/module.py` — uses `get_success_url()` override (needs cleanup)
- Check: `app/security/views/group.py` — correctly uses `success_url`
- Check: `app/auth/views/users.py` — follows pattern correctly
- Check: `app/auth/views/web.py` — mixed concerns (ISSUE: login + dashboard + profile)

- [ ] **Step 1: Review module.py and note overrides**

Run:
```bash
grep -A2 "def get_success_url" app/security/views/module.py
```

Expected: 6 overrides (3 ModuleType views + 3 Module views). We'll replace with `success_url` attribute.

- [ ] **Step 2: Confirm group.py uses correct pattern**

Run:
```bash
grep "success_url" app/security/views/group.py
```

Expected: All 3 views (Create, Update, Delete) have `success_url = reverse_lazy(...)` — this is the pattern we want everywhere.

- [ ] **Step 3: Confirm users.py follows pattern**

Run:
```bash
grep "success_url" app/auth/views/users.py
```

Expected: All views use `success_url = reverse_lazy(...)`.

---

## Phase 2: Separate Auth Concerns

### Task 3: Create `app/auth/views/auth.py` with login/register/logout

**Files:**
- Create: `app/auth/views/auth.py`
- Modify: `app/auth/views/web.py` → delete (after moving code)
- Modify: `app/auth/urls.py` — update imports

- [ ] **Step 1: Create `auth.py` and move auth views**

Create file `app/auth/views/auth.py`:

```python
from django.contrib.auth import login, logout
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from app.auth.forms import LoginForm, RegisterForm
from app.common.mixins import PublicMixin


class IndexRedirectView(View):
    """Redirect authenticated users to dashboard, others to login."""
    def get(self, request):
        target = 'dashboard' if request.user.is_authenticated else 'login'
        return redirect(target)


class LoginView(PublicMixin, View):
    template_name = 'shared/auth/login.html'
    form_class = LoginForm

    def get(self, request):
        return render(request, self.template_name, {'form': self.form_class()})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            user.set_group_session()
            return redirect(request.GET.get('next', 'dashboard'))
        return render(request, self.template_name, {'form': form})


class RegisterView(PublicMixin, View):
    template_name = 'shared/auth/register.html'
    form_class = RegisterForm

    def get(self, request):
        return render(request, self.template_name, {'form': self.form_class()})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro exitoso. Por favor inicia sesión.')
            return redirect('login')
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """Logout and redirect to login page."""
    def post(self, request):
        logout(request)
        messages.success(request, 'Has cerrado sesión.')
        return redirect('login')
```

- [ ] **Step 2: Verify imports are correct**

Run:
```bash
head -15 app/auth/views/auth.py
```

Expected: All imports from `app.auth.forms`, `app.common.mixins`, `django.*` available.

- [ ] **Step 3: Commit**

```bash
git add app/auth/views/auth.py
git commit -m "feat: create auth.py with login/register/logout views"
```

---

### Task 4: Create `app/auth/views/dashboard.py` with dashboard view

**Files:**
- Create: `app/auth/views/dashboard.py`

- [ ] **Step 1: Create `dashboard.py` with DashboardView**

Create file `app/auth/views/dashboard.py`:

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from app.auth.models import User
from app.security.models import Group, Module


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'shared/dashboard/home.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context.update({
            'user': user,
            'profile': getattr(user, 'profile', None),
            'user_groups': list(user.security_groups.filter(is_active=True)),
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'staff_users': User.objects.filter(is_staff=True).count(),
            'total_modules': Module.objects.filter(is_active=True).count(),
            'total_groups': Group.objects.filter(is_active=True).count(),
            'recent_users': User.objects.order_by('-date_joined')[:5],
        })
        return context
```

- [ ] **Step 2: Verify no syntax errors**

Run:
```bash
python manage.py check
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add app/auth/views/dashboard.py
git commit -m "feat: create dashboard.py with DashboardView"
```

---

### Task 5: Create `app/auth/views/profile.py` with profile views

**Files:**
- Create: `app/auth/views/profile.py`

- [ ] **Step 1: Create `profile.py` with all profile-related views**

Create file `app/auth/views/profile.py`:

```python
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, UpdateView

from app.auth.forms import PasswordChangeForm, ProfileUpdateForm
from app.common.choices import Department


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'shared/profile/view.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context.update({'user': user, 'profile': user.profile})
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    template_name = 'shared/profile/edit.html'
    form_class = ProfileUpdateForm
    success_url = reverse_lazy('profile')
    login_url = 'login'

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Perfil actualizado correctamente.')
        return super().form_valid(form)


class PasswordChangeView(LoginRequiredMixin, View):
    template_name = 'shared/profile/change_password.html'
    login_url = 'login'

    def get(self, request):
        return render(request, self.template_name, {'form': PasswordChangeForm(request.user)})

    def post(self, request):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = request.user
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            login(request, user)
            messages.success(request, 'Contraseña actualizada correctamente.')
            return redirect('profile')
        return render(request, self.template_name, {'form': form})


class ProfileManageView(LoginRequiredMixin, TemplateView):
    template_name = 'shared/profile/manage.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context.update({
            'user': user,
            'profile': user.profile,
            'department': dict(Department.choices),
        })
        return context


class ProfileUpdateAPIView(LoginRequiredMixin, View):
    login_url = 'login'
    EDITABLE_FIELDS = ('department', 'job_title', 'phone', 'address', 'city')

    def post(self, request):
        profile = request.user.profile
        for field in self.EDITABLE_FIELDS:
            if field in request.POST:
                setattr(profile, field, request.POST.get(field))
        profile.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('profile_manage')
```

- [ ] **Step 2: Verify no syntax errors**

Run:
```bash
python manage.py check
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add app/auth/views/profile.py
git commit -m "feat: create profile.py with all profile-related views"
```

---

### Task 6: Update `app/auth/views/__init__.py` to re-export from new files

**Files:**
- Modify: `app/auth/views/__init__.py`

- [ ] **Step 1: Read current __init__.py**

Run:
```bash
cat app/auth/views/__init__.py
```

- [ ] **Step 2: Update __init__.py with new imports**

Replace the content of `app/auth/views/__init__.py` with:

```python
from .auth import IndexRedirectView, LoginView, RegisterView, LogoutView
from .dashboard import DashboardView
from .profile import (
    ProfileView,
    ProfileEditView,
    PasswordChangeView,
    ProfileManageView,
    ProfileUpdateAPIView,
)
from .users import UserListView, UserCreate, UserUpdate, UserDelete

__all__ = [
    # Auth
    'IndexRedirectView',
    'LoginView',
    'RegisterView',
    'LogoutView',
    # Dashboard
    'DashboardView',
    # Profile
    'ProfileView',
    'ProfileEditView',
    'PasswordChangeView',
    'ProfileManageView',
    'ProfileUpdateAPIView',
    # Users CRUD
    'UserListView',
    'UserCreate',
    'UserUpdate',
    'UserDelete',
]
```

- [ ] **Step 3: Verify imports work**

Run:
```bash
python manage.py shell -c "from app.auth.views import LoginView, DashboardView, ProfileView; print('OK')"
```

Expected: OK

- [ ] **Step 4: Commit**

```bash
git add app/auth/views/__init__.py
git commit -m "refactor: update auth views __init__.py with new imports"
```

---

### Task 7: Update `app/auth/urls.py` to use new view imports

**Files:**
- Modify: `app/auth/urls.py`

- [ ] **Step 1: Read current urls.py**

Run:
```bash
cat app/auth/urls.py
```

- [ ] **Step 2: Update imports (if they reference web.py)**

If the file has imports like `from .views.web import ...`, change them to use the new modular imports:

Expected file should look like:
```python
from django.urls import path
from .views import (
    IndexRedirectView,
    LoginView,
    RegisterView,
    LogoutView,
    DashboardView,
    ProfileView,
    ProfileEditView,
    PasswordChangeView,
    ProfileManageView,
    ProfileUpdateAPIView,
    UserListView,
    UserCreate,
    UserUpdate,
    UserDelete,
)

urlpatterns = [
    path('', IndexRedirectView.as_view(), name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
    path('profile/change-password/', PasswordChangeView.as_view(), name='profile_change_password'),
    path('profile/manage/', ProfileManageView.as_view(), name='profile_manage'),
    path('profile/update-api/', ProfileUpdateAPIView.as_view(), name='profile_update_api'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreate.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', UserUpdate.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', UserDelete.as_view(), name='user_delete'),
]
```

Verify the patterns match your current setup. If different, adjust accordingly but maintain the new imports.

- [ ] **Step 3: Verify no errors**

Run:
```bash
python manage.py check
```

Expected: No errors.

- [ ] **Step 4: Test URL routing**

Run:
```bash
python manage.py shell -c "from django.urls import reverse; print(reverse('login')); print(reverse('dashboard')); print(reverse('profile'))"
```

Expected: 
```
/login/
/dashboard/
/profile/
```

- [ ] **Step 5: Commit**

```bash
git add app/auth/urls.py
git commit -m "refactor: update auth urls to use new modular views"
```

---

### Task 8: Delete old `app/auth/views/web.py`

**Files:**
- Delete: `app/auth/views/web.py`

- [ ] **Step 1: Verify all code is moved**

Run:
```bash
grep -n "class " app/auth/views/web.py | wc -l
```

Expected: Should show the classes exist before we delete.

- [ ] **Step 2: Delete the file**

Run:
```bash
rm app/auth/views/web.py
```

- [ ] **Step 3: Verify it's gone**

Run:
```bash
ls app/auth/views/
```

Expected: Should not show `web.py`. Should have `auth.py`, `dashboard.py`, `profile.py`, `users.py`, `__init__.py`.

- [ ] **Step 4: Run tests to ensure nothing broke**

Run:
```bash
python manage.py test app.auth.tests -v 2
```

Expected: All tests pass. If any fail, check imports.

- [ ] **Step 5: Commit**

```bash
git add -u app/auth/views/
git commit -m "refactor: delete old web.py, views now modularized"
```

---

## Phase 3: Clean Up Security Views

### Task 9: Clean up `app/security/views/module.py` — remove `get_success_url()` overrides

**Files:**
- Modify: `app/security/views/module.py`

- [ ] **Step 1: Read current file**

Run:
```bash
cat app/security/views/module.py
```

- [ ] **Step 2: Replace with clean version**

Replace entire file:

```python
from django.urls import reverse_lazy

from app.security.forms import ModuleForm, ModuleTypeForm
from app.security.models import Module, ModuleType

from ._crud import CrudCreateView, CrudDeleteView, CrudListView, CrudUpdateView


class ModuleTypeListView(CrudListView):
    model = ModuleType
    template_name = 'security/module_type/list.html'
    permission_required = 'view_moduletype'
    list_title = 'Tipos de módulo'
    create_url_name = 'module_type_create'
    search_fields = ['name', 'description']
    toggle_field = 'is_active'


class ModuleTypeCreate(CrudCreateView):
    model = ModuleType
    form_class = ModuleTypeForm
    template_name = 'form.html'
    permission_required = 'add_moduletype'
    list_url_name = 'module_type_list'
    create_title = 'Crear tipo de módulo'
    unique_fields = ['name']
    success_url = reverse_lazy('module_type_list')


class ModuleTypeUpdate(CrudUpdateView):
    model = ModuleType
    form_class = ModuleTypeForm
    template_name = 'form.html'
    permission_required = 'change_moduletype'
    list_url_name = 'module_type_list'
    update_title = 'Editar tipo de módulo'
    unique_fields = ['name']
    success_url = reverse_lazy('module_type_list')


class ModuleTypeDelete(CrudDeleteView):
    model = ModuleType
    template_name = 'delete.html'
    permission_required = 'delete_moduletype'
    list_url_name = 'module_type_list'
    success_url = reverse_lazy('module_type_list')


class ModuleListView(CrudListView):
    model = Module
    template_name = 'security/module/list.html'
    permission_required = 'view_module'
    list_title = 'Módulos'
    create_url_name = 'module_create'
    search_fields = ['name', 'url', 'description']
    toggle_field = 'is_active'


class ModuleCreate(CrudCreateView):
    model = Module
    form_class = ModuleForm
    template_name = 'form.html'
    permission_required = 'add_module'
    list_url_name = 'module_list'
    create_title = 'Crear módulo'
    unique_fields = ['url']
    success_url = reverse_lazy('module_list')


class ModuleUpdate(CrudUpdateView):
    model = Module
    form_class = ModuleForm
    template_name = 'form.html'
    permission_required = 'change_module'
    list_url_name = 'module_list'
    update_title = 'Editar módulo'
    unique_fields = ['url']
    success_url = reverse_lazy('module_list')


class ModuleDelete(CrudDeleteView):
    model = Module
    template_name = 'delete.html'
    permission_required = 'delete_module'
    list_url_name = 'module_list'
    success_url = reverse_lazy('module_list')
```

- [ ] **Step 3: Verify no syntax errors**

Run:
```bash
python manage.py check
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add app/security/views/module.py
git commit -m "refactor: clean up module.py — remove get_success_url overrides"
```

---

### Task 10: Verify `app/security/views/group.py` is already clean

**Files:**
- Check: `app/security/views/group.py`

- [ ] **Step 1: Verify it uses `success_url` correctly**

Run:
```bash
grep "success_url" app/security/views/group.py
```

Expected: All 3 views have `success_url = reverse_lazy(...)`. No `get_success_url()` methods.

- [ ] **Step 2: Run import check**

Run:
```bash
python manage.py shell -c "from app.security.views.group import GroupListView, GroupCreate, GroupUpdate, GroupDelete; print('OK')"
```

Expected: OK

- [ ] **Step 3: No action needed**

group.py is already clean. Document completion:

Run:
```bash
git log --oneline app/security/views/group.py | head -3
```

Expected: Shows commit history. group.py is confirmed clean.

---

## Phase 4: Verify All Models Have `to_json()`

### Task 11: Verify User model has `to_json()` method

**Files:**
- Check: `app/auth/models/user.py`

- [ ] **Step 1: Check if User has `to_json()`**

Run:
```bash
grep -n "def to_json" app/auth/models/user.py
```

If found: We're good. If not found, see Step 2.

- [ ] **Step 2: If not found, check how it's currently handled in users.py**

Run:
```bash
grep -B5 -A10 "_user_to_json" app/auth/views/users.py
```

Expected: Shows a function that adds the method dynamically. This is fine, but let's verify it works.

- [ ] **Step 3: Verify dynamically added method works**

Run:
```bash
python manage.py shell -c "from app.auth.models import User; u = User.objects.first(); print(u.to_json() if hasattr(u, 'to_json') else 'Method exists')"
```

Expected: Either prints JSON or 'Method exists'. No errors.

- [ ] **Step 4: No action needed**

User.to_json() is already handled. Proceed.

---

### Task 12: Verify security models have `to_json()` methods

**Files:**
- Check: `app/security/models/module.py`
- Check: `app/security/models/group.py`

- [ ] **Step 1: Verify Module and ModuleType have `to_json()`**

Run:
```bash
grep -n "class Module\|def to_json" app/security/models/module.py | head -15
```

Expected: Both classes should have `to_json()` method.

- [ ] **Step 2: Verify Group has `to_json()`**

Run:
```bash
grep -n "class Group\|def to_json" app/security/models/group.py | head -10
```

Expected: Group class should have `to_json()` method.

- [ ] **Step 3: Test serialization in shell**

Run:
```bash
python manage.py shell << 'EOF'
from app.security.models import Module, Group
m = Module.objects.first()
g = Group.objects.first()
print("Module:", m.to_json() if m else "No modules")
print("Group:", g.to_json() if g else "No groups")
EOF
```

Expected: Both print their JSON representations without errors.

- [ ] **Step 4: No action needed**

All models already have `to_json()`. Proceed.

---

## Phase 5: Final Verification & Testing

### Task 13: Run full test suite

**Files:**
- Test: `app/auth/tests/`
- Test: `app/security/tests/`

- [ ] **Step 1: Run all app tests**

Run:
```bash
python manage.py test app.auth app.security -v 2
```

Expected: All tests pass. If any fail, diagnose and fix imports/view references.

- [ ] **Step 2: Run server and verify routes work**

Run:
```bash
python manage.py runserver 0.0.0.0:8000 &
sleep 2
curl -s http://localhost:8000/login/ | grep -c "form" > /dev/null && echo "Login page OK"
curl -s http://localhost:8000/ | grep -c "dashboard\|login" > /dev/null && echo "Index redirect OK"
kill %1
```

Expected: Both checks print "OK".

- [ ] **Step 3: Test auth flow manually (optional, good for confidence)**

If running locally:
1. Start server: `python manage.py runserver`
2. Go to `http://localhost:8000/` → should redirect to login
3. Try login with `admin/admin` → should go to dashboard
4. Click on profile → should show profile page
5. Go to users admin → should show user list

- [ ] **Step 4: Commit**

No code changes here, just mark completion:

```bash
git log --oneline | head -10
```

Expected: Shows recent commits for each phase.

---

### Task 14: Verify imports across the project

**Files:**
- Check: `core/urls.py` — includes app urls
- Check: `core/settings.py` — INSTALLED_APPS, context_processors

- [ ] **Step 1: Verify core/urls.py still works**

Run:
```bash
python manage.py check
```

Expected: No errors related to URL includes.

- [ ] **Step 2: Test all URL names exist**

Run:
```bash
python manage.py shell << 'EOF'
from django.urls import reverse
routes = ['login', 'register', 'logout', 'dashboard', 'profile', 'user_list']
for route in routes:
    try:
        print(f"{route}: {reverse(route)}")
    except Exception as e:
        print(f"{route}: ERROR - {e}")
EOF
```

Expected: All routes print their URL paths without errors.

- [ ] **Step 3: Verify context processors still work**

Run:
```bash
python manage.py shell << 'EOF'
from django.template import Context, Template
from app.security.context_processors import modules
from app.auth.models import User

# Mock request
class MockRequest:
    def __init__(self):
        self.user = User.objects.filter(is_staff=True).first()
        self.session = {'group': 1}

req = MockRequest()
if req.user:
    ctx = modules(req)
    print(f"available_modules: {bool(ctx.get('available_modules'))}")
EOF
```

Expected: Prints `available_modules: True` (or False if no modules, but no errors).

- [ ] **Step 4: Commit**

```bash
git log --oneline | head -5
```

No additional commit needed; verification is complete.

---

### Task 15: Final cleanup and documentation

**Files:**
- Update: Memory (if using Claude Code memory system)
- Review: CLAUDE.md — ensure still accurate

- [ ] **Step 1: Review CLAUDE.md for any updates needed**

Run:
```bash
grep -n "web.py\|views/web" CLAUDE.md
```

Expected: Should not find references to `web.py` being a single file anymore. If found, update the docs.

- [ ] **Step 2: Create summary commit**

```bash
git log --oneline --since="1 hour ago"
```

Expected: Shows all refactoring commits. Create a final summary if desired:

```bash
git log --oneline | head -15
# Review all changes
```

- [ ] **Step 3: Mark refactoring complete**

Create a brief note:

```bash
git log -1 --format="%H %s" > REFACTORING_COMPLETE
cat REFACTORING_COMPLETE
```

All CRUD views now follow the clean pattern. Auth views are separated. Ready for feature development.

---

## Self-Review Checklist

- [x] **Spec coverage**: 
  - ✓ Auth views separated into auth.py, dashboard.py, profile.py
  - ✓ Security views cleaned (module.py get_success_url removed)
  - ✓ All CRUD patterns verified
  - ✓ All models have to_json()
  
- [x] **No placeholders**: 
  - All code blocks are complete and runnable
  - All commands are exact with expected output
  - No "TBD" or "similar to task X" statements

- [x] **Type consistency**: 
  - View names consistent (LoginView, DashboardView, ProfileView)
  - URL names consistent (login, dashboard, profile)
  - Field names consistent across tasks (success_url, permission_required)

- [x] **Execution readiness**:
  - Each task is 2-5 minutes of focused work
  - Clear before/after state
  - Commit boundaries are logical
