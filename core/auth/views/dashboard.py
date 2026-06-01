from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from core.auth.models import User
from core.security.models import Group, Module


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'
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


__all__ = ['DashboardView']
