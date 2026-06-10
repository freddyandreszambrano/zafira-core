from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import TemplateView

from core.auth.models import User
from core.security.models import Group, Module


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        new_users_30d = User.objects.filter(
            date_joined__gte=timezone.now() - timedelta(days=30),
        ).count()

        total_modules = Module.objects.filter(is_active=True).count()

        context.update(
            {
                "user": user,
                "profile": getattr(user, "profile", None),
                "user_groups": list(user.security_groups.filter(is_active=True)),
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
                "active_pct": round(active_users / total_users * 100) if total_users else 0,
                "new_users_30d": new_users_30d,
                "staff_users": User.objects.filter(is_staff=True).count(),
                "superusers": User.objects.filter(is_superuser=True).count(),
                "total_modules": total_modules,
                "visible_modules": Module.objects.filter(is_active=True, is_visible=True).count(),
                "total_groups": Group.objects.filter(is_active=True).count(),
                "recent_users": User.objects.order_by("-date_joined")[:5],
                "group_distribution": self._group_distribution(),
                "account_health": self._account_health(active_users, total_users - active_users),
            }
        )
        return context

    def _group_distribution(self):
        groups = (
            Group.objects.filter(is_active=True)
            .annotate(
                members_total=Count("members", filter=Q(members__is_active=True), distinct=True),
                modules_total=Count("modules", distinct=True),
            )
            .order_by("-members_total", "name")[:6]
        )
        # La barra es relativa al grupo más poblado, no al total de usuarios.
        top = max((g.members_total for g in groups), default=0)
        return [
            {
                "name": g.name,
                "members": g.members_total,
                "modules": g.modules_total,
                "share": round(g.members_total / top * 100) if top else 0,
            }
            for g in groups
        ]

    def _account_health(self, active_users, inactive_users):
        need_password = User.objects.filter(is_active=True, force_password_change=True).count()
        never_logged_in = User.objects.filter(is_active=True, last_login__isnull=True).count()
        return [
            {
                "label": "Cambio de contraseña pendiente",
                "icon": "fas fa-key",
                "value": need_password,
                "level": "danger" if need_password else "ok",
            },
            {
                "label": "Sin primer acceso",
                "icon": "fas fa-user-clock",
                "value": never_logged_in,
                "level": "warn" if never_logged_in else "ok",
            },
            {
                "label": "Cuentas inactivas",
                "icon": "fas fa-user-slash",
                "value": inactive_users,
                "level": "warn" if inactive_users else "ok",
            },
            {
                "label": "Cuentas activas",
                "icon": "fas fa-user-check",
                "value": active_users,
                "level": "info",
            },
        ]


__all__ = ["DashboardView"]
