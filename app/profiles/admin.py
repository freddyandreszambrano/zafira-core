"""Admin interface for user profiles."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Custom admin for UserProfile."""

    fieldsets = (
        (None, {'fields': ('user',)}),
        (_('Información de Contacto'), {
            'fields': ('phone', 'address', 'city', 'country'),
        }),
        (_('Información Profesional'), {
            'fields': ('department', 'job_title', 'manager', 'employee_id', 'hire_date'),
        }),
        (_('Información Adicional'), {
            'fields': ('bio', 'social_media', 'is_verified'),
            'classes': ('collapse',),
        }),
        (_('Fechas'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    list_display = (
        'get_username', 'get_email', 'get_full_name', 'job_title',
        'department', 'is_verified', 'created_at'
    )
    list_filter = ('department', 'is_verified', 'created_at', 'hire_date')
    search_fields = (
        'user__username', 'user__email', 'user__first_name',
        'user__last_name', 'job_title', 'employee_id'
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    def get_username(self, obj):
        """Display user's username."""
        return obj.user.username

    get_username.short_description = 'Usuario'

    def get_email(self, obj):
        """Display user's email."""
        return obj.user.email

    get_email.short_description = 'Correo'

    def get_full_name(self, obj):
        """Display user's full name."""
        return obj.user.get_full_name()

    get_full_name.short_description = 'Nombre Completo'

    actions = ['mark_as_verified', 'mark_as_unverified']

    def mark_as_verified(self, request, queryset):
        """Admin action to mark profiles as verified."""
        count = queryset.update(is_verified=True)
        self.message_user(request, f'{count} perfil(es) marcado(s) como verificado(s).')

    mark_as_verified.short_description = 'Marcar como verificado'

    def mark_as_unverified(self, request, queryset):
        """Admin action to mark profiles as unverified."""
        count = queryset.update(is_verified=False)
        self.message_user(request, f'{count} perfil(es) marcado(s) como no verificado(s).')

    mark_as_unverified.short_description = 'Marcar como no verificado'
