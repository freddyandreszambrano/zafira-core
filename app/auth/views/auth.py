from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from app.auth.forms import LoginForm, RegisterForm
from app.common.mixins import PublicMixin


class IndexRedirectView(View):
    """
    Redirect to dashboard if authenticated, otherwise to login.
    Serves as the root entry point for the application.
    """

    def get(self, request):
        target = 'dashboard' if request.user.is_authenticated else 'login'
        return redirect(target)


class LoginView(PublicMixin, View):
    """
    Handle user login with form validation and session initialization.
    Sets the active group in session via set_group_session().
    Supports 'next' URL parameter for post-login redirect.
    """

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
    """
    Handle user registration with form validation.
    Creates a new User account and redirects to login with success message.
    """

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


class LogoutView(LoginRequiredMixin, View):
    """
    Handle user logout and session cleanup.
    Requires authentication; redirects to login after logout.
    """

    login_url = 'login'

    def post(self, request):
        logout(request)
        messages.success(request, 'Has cerrado sesión.')
        return redirect('login')
