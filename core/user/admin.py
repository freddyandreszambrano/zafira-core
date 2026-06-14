from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Informacion Personal"),
            {
                "fields": ("first_name", "last_name", "email", "dni", "image", "user_type"),
            },
        ),
        (
            _("Permisos"),
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        (
            _("Seguridad"),
            {
                "fields": ("force_password_change", "is_change_password", "email_reset_token"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Fechas Importantes"),
            {
                "fields": ("last_login", "date_joined", "last_password_change_at"),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "dni",
                    "first_name",
                    "last_name",
                    "user_type",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    list_display = (
        "username",
        "email",
        "dni",
        "user_type",
        "get_full_name",
        "is_active",
        "is_staff",
        "date_joined",
        "last_login",
    )
    list_filter = (
        "user_type",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
        "last_login",
    )
    search_fields = ("username", "email", "dni", "first_name", "last_name")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login", "last_password_change_at")

    actions = ["activate_users", "deactivate_users", "reset_password_flag"]

    @admin.display(description="Nombre Completo")
    def get_full_name(self, obj):
        return obj.get_full_name() or "---"

    @admin.action(description="Activar usuarios seleccionados")
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} usuario(s) activado(s).")

    @admin.action(description="Desactivar usuarios seleccionados")
    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} usuario(s) desactivado(s).")

    @admin.action(description="Marcar para cambio de contrasena")
    def reset_password_flag(self, request, queryset):
        count = queryset.update(force_password_change=True)
        self.message_user(request, f"{count} usuario(s) marcado(s) para cambio de contrasena.")
