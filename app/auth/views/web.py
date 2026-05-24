from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView, UpdateView

from app.auth.forms import LoginForm, PasswordChangeForm, ProfileUpdateForm, RegisterForm
from app.common.choices import Department
from app.common.mixins import PublicMixin


class IndexRedirectView(View):
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
            login(request, form.get_user())
            return redirect(request.GET.get('next', 'dashboard'))
        return render(request, self.template_name, {'form': form})


class RegisterView(PublicMixin, CreateView):
    template_name = 'shared/auth/register.html'
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
    template_name = 'shared/dashboard/home.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context.update({
            'user': user,
            'profile': user.profile,
            'groups': user.groups.all(),
        })
        return context


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
