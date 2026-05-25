from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, UpdateView

from app.auth.forms import PasswordChangeForm, ProfileUpdateForm
from app.common.choices import Department


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'shared/dashboard/home.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        from app.auth.models import User
        from app.security.models import Group, Module

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
