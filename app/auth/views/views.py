from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView

from app.auth.models import User
from app.auth.forms import LoginForm, RegisterForm, ProfileUpdateForm, PasswordChangeForm


class PublicMixin(UserPassesTestMixin):
    def test_func(self):
        return not self.request.user.is_authenticated

    def handle_no_permission(self):
        return redirect('dashboard')


class LoginView(PublicMixin, View):
    template_name = 'web/auth/login.html'
    form_class = LoginForm

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        return render(request, self.template_name, {'form': form})


class RegisterView(PublicMixin, CreateView):
    template_name = 'web/auth/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Registro exitoso. Por favor inicia sesión.')
        return response


class LogoutView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request):
        logout(request)
        messages.success(request, 'Has cerrado sesión.')
        return redirect('login')


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'web/dashboard/home.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        context['profile'] = user.profile
        context['groups'] = user.groups.all()
        return context


class UsersListView(LoginRequiredMixin, TemplateView):
    template_name = 'web/users/list.html'
    login_url = 'login'

    def test_func(self):
        return self.request.user.groups.filter(name__in=['Admin', 'Manager']).exists()

    def get(self, request, *args, **kwargs):
        if not self.test_func():
            return HttpResponseForbidden('No tienes permiso para acceder.')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search = self.request.GET.get('search', '')

        users = User.objects.filter(is_active=True)
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        context['users'] = users
        context['search'] = search
        return context


class UserDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'web/users/detail.html'
    login_url = 'login'

    def test_func(self):
        user_id = self.kwargs.get('pk')
        user = get_object_or_404(User, pk=user_id)
        is_admin = self.request.user.groups.filter(name='Admin').exists()
        return is_admin or self.request.user.pk == user.pk

    def get(self, request, *args, **kwargs):
        if not self.test_func():
            return HttpResponseForbidden('No tienes permiso para acceder.')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(User, pk=self.kwargs['pk'])
        context['user'] = user
        context['profile'] = user.profile
        context['groups'] = user.groups.all()
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'web/profile/view.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        context['profile'] = user.profile
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    template_name = 'web/profile/edit.html'
    form_class = ProfileUpdateForm
    success_url = reverse_lazy('profile')
    login_url = 'login'

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Perfil actualizado correctamente.')
        return super().form_valid(form)


class PasswordChangeView(LoginRequiredMixin, View):
    template_name = 'web/profile/change_password.html'
    login_url = 'login'

    def get(self, request):
        form = PasswordChangeForm(request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = request.user
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            messages.success(request, 'Contraseña actualizada correctamente.')
            login(request, user)
            return redirect('profile')
        return render(request, self.template_name, {'form': form})


class ProfileManageView(LoginRequiredMixin, TemplateView):
    template_name = 'web/profile/manage.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile = user.profile
        context['user'] = user
        context['profile'] = profile
        context['department'] = dict(profile.DEPARTMENT_CHOICES)
        return context


class ProfileUpdateAPIView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request):
        user = request.user
        profile = user.profile

        if 'department' in request.POST:
            profile.department = request.POST.get('department')
        if 'job_title' in request.POST:
            profile.job_title = request.POST.get('job_title')
        if 'phone' in request.POST:
            profile.phone = request.POST.get('phone')
        if 'address' in request.POST:
            profile.address = request.POST.get('address')
        if 'city' in request.POST:
            profile.city = request.POST.get('city')

        profile.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('profile_manage')


# AJAX API Views for User Management

class ListUsersAjaxView(LoginRequiredMixin, View):
    """AJAX endpoint to list users with pagination"""
    login_url = 'login'
    
    def get(self, request):
        if not request.user.is_staff:
            return JsonResponse({'error': 'Permiso denegado'}, status=403)
        
        page = request.GET.get('page', 1)
        search = request.GET.get('search', '')
        
        from django.core.paginator import Paginator
        from django.http import JsonResponse
        
        # Filter users
        queryset = User.objects.all()
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Paginate
        paginator = Paginator(queryset.order_by('-date_joined'), 10)
        users_page = paginator.get_page(page)
        
        users_data = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M'),
            }
            for user in users_page
        ]
        
        return JsonResponse({
            'users': users_data,
            'page': users_page.number,
            'total_pages': paginator.num_pages,
            'total_count': queryset.count(),
        })


class EditUserAjaxView(LoginRequiredMixin, View):
    """AJAX endpoint to edit user"""
    login_url = 'login'
    
    def post(self, request):
        from django.http import JsonResponse
        
        if not request.user.is_staff:
            return JsonResponse({'error': 'Permiso denegado'}, status=403)
        
        try:
            user_id = request.POST.get('user_id')
            user = User.objects.get(pk=user_id)
            
            # Import EditUserForm
            from app.auth.forms import EditUserForm
            form = EditUserForm(request.POST, instance=user)
            
            if form.is_valid():
                form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Usuario actualizado',
                })
            else:
                errors = {field: str(error[0]) for field, error in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors}, status=400)
        
        except User.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class DeleteUserAjaxView(LoginRequiredMixin, View):
    """AJAX endpoint to delete user"""
    login_url = 'login'
    
    def post(self, request):
        from django.http import JsonResponse
        
        if not request.user.is_staff:
            return JsonResponse({'error': 'Permiso denegado'}, status=403)
        
        if request.user.id == int(request.POST.get('user_id', 0)):
            return JsonResponse({'error': 'No puedes eliminarte a ti mismo'}, status=400)
        
        try:
            user_id = request.POST.get('user_id')
            user = User.objects.get(pk=user_id)
            user.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Usuario eliminado',
            })
        
        except User.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class ChangePasswordAjaxView(LoginRequiredMixin, View):
    """AJAX endpoint to change password"""
    login_url = 'login'
    
    def post(self, request):
        from django.http import JsonResponse
        from app.auth.forms import PasswordChangeForm, ResetPasswordForm
        
        try:
            user_id = request.POST.get('user_id')
            
            if not request.user.is_staff and request.user.id != int(user_id):
                return JsonResponse({'error': 'Permiso denegado'}, status=403)
            
            user = User.objects.get(pk=user_id)
            
            if request.user.is_staff:
                form = ResetPasswordForm(request.POST)
            else:
                form = PasswordChangeForm(user, request.POST)
            
            if form.is_valid():
                new_password = form.cleaned_data.get('new_password')
                user.set_password(new_password)
                user.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Contraseña cambiada',
                })
            else:
                errors = {field: str(error[0]) for field, error in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors}, status=400)
        
        except User.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class ResetPasswordAjaxView(LoginRequiredMixin, View):
    """AJAX endpoint for admin to reset user password"""
    login_url = 'login'
    
    def post(self, request):
        from django.http import JsonResponse
        from app.auth.forms import ResetPasswordForm
        
        if not request.user.is_staff:
            return JsonResponse({'error': 'Permiso denegado'}, status=403)
        
        try:
            user_id = request.POST.get('user_id')
            user = User.objects.get(pk=user_id)
            
            form = ResetPasswordForm(request.POST)
            if form.is_valid():
                new_password = form.cleaned_data.get('new_password')
                user.set_password(new_password)
                user.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Contraseña reseteada',
                })
            else:
                errors = {field: str(error[0]) for field, error in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors}, status=400)
        
        except User.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class IndexRedirectView(View):
    """Redirige a login o dashboard según autenticación"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return redirect('login')


class RegisterView(View):
    """Handle user registration"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        
        from app.auth.forms import RegisterForm
        form = RegisterForm()
        return render(request, 'web/auth/register.html', {'form': form})
    
    def post(self, request):
        from app.auth.forms import RegisterForm
        form = RegisterForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
        
        return render(request, 'web/auth/register.html', {'form': form})
