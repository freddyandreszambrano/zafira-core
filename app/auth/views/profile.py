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
    template_name = 'profile/view.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'user': self.request.user, 'profile': self.request.user.profile})
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    template_name = 'profile/edit.html'
    form_class = ProfileUpdateForm
    success_url = reverse_lazy('profile')
    login_url = 'login'

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Perfil actualizado correctamente.')
        return super().form_valid(form)


class PasswordChangeView(LoginRequiredMixin, View):
    template_name = 'profile/change_password.html'
    login_url = 'login'

    def get(self, request):
        context = {
            'form': PasswordChangeForm(request.user),
            'title': 'Cambiar contraseña',
            'list_url': reverse_lazy('profile'),
            'action': 'change',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = request.user
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            login(request, user)
            messages.success(request, 'Contraseña actualizada correctamente.')
            return redirect('profile')
        context = {
            'form': form,
            'title': 'Cambiar contraseña',
            'list_url': reverse_lazy('profile'),
            'action': 'change',
        }
        return render(request, self.template_name, context)


class ProfileManageView(LoginRequiredMixin, View):
    template_name = 'profile/manage.html'
    login_url = 'login'
    EDITABLE_FIELDS = ('department', 'job_title', 'phone', 'address', 'city')

    def get(self, request):
        context = {
            'user': request.user,
            'profile': request.user.profile,
            'departments': Department.choices,
            'title': 'Datos corporativos',
            'list_url': reverse_lazy('profile'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        profile = request.user.profile
        for field in self.EDITABLE_FIELDS:
            if field in request.POST:
                setattr(profile, field, request.POST.get(field))
        profile.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('profile')


__all__ = ['ProfileView', 'ProfileEditView', 'PasswordChangeView', 'ProfileManageView']
