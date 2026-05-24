from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with enhanced configuration."""

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Información Personal'), {
            'fields': ('first_name', 'last_name', 'email', 'dni', 'image')
        }),
        (_('Permisos'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Seguridad'), {
            'fields': ('force_password_change', 'is_change_password', 'email_reset_token'),
            'classes': ('collapse',),
        }),
        (_('Fechas Importantes'), {
            'fields': ('last_login', 'date_joined', 'last_password_change_at'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'dni', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    list_display = (
        'username', 'email', 'dni', 'get_full_name', 'is_active',
        'is_staff', 'date_joined', 'last_login'
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    search_fields = ('username', 'email', 'dni', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login', 'last_password_change_at')

    def get_full_name(self, obj):
        """Display full name in list view."""
        return obj.get_full_name() or '---'

    get_full_name.short_description = 'Nombre Completo'

    actions = ['activate_users', 'deactivate_users', 'reset_password_flag']

    def activate_users(self, request, queryset):
        """Admin action to activate selected users."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} usuario(s) activado(s).')

    activate_users.short_description = 'Activar usuarios seleccionados'

    def deactivate_users(self, request, queryset):
        """Admin action to deactivate selected users."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} usuario(s) desactivado(s).')

    deactivate_users.short_description = 'Desactivar usuarios seleccionados'

    def reset_password_flag(self, request, queryset):
        """Admin action to flag users for password reset."""
        count = queryset.update(force_password_change=True)
        self.message_user(request, f'{count} usuario(s) marcado(s) para cambio de contraseña.')

    reset_password_flag.short_description = 'Marcar para cambio de contraseña'
