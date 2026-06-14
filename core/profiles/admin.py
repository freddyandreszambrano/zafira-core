from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import MobileProfile, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("user",)}),
        (_("Informacion de Contacto"), {"fields": ("phone", "address", "city", "country")}),
        (
            _("Informacion Profesional"),
            {"fields": ("department", "job_title", "manager", "employee_id", "hire_date")},
        ),
        (
            _("Informacion Adicional"),
            {"fields": ("bio", "social_media", "is_verified"), "classes": ("collapse",)},
        ),
        (_("Fechas"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    list_display = (
        "get_username",
        "get_email",
        "get_full_name",
        "job_title",
        "department",
        "is_verified",
        "created_at",
    )
    list_filter = ("department", "is_verified", "created_at", "hire_date")
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "job_title",
        "employee_id",
    )
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    actions = ["mark_as_verified", "mark_as_unverified"]

    @admin.display(description="Usuario")
    def get_username(self, obj):
        return obj.user.username

    @admin.display(description="Correo")
    def get_email(self, obj):
        return obj.user.email

    @admin.display(description="Nombre Completo")
    def get_full_name(self, obj):
        return obj.user.get_full_name()

    @admin.action(description="Marcar como verificado")
    def mark_as_verified(self, request, queryset):
        count = queryset.update(is_verified=True)
        self.message_user(request, f"{count} perfil(es) marcado(s) como verificado(s).")

    @admin.action(description="Marcar como no verificado")
    def mark_as_unverified(self, request, queryset):
        count = queryset.update(is_verified=False)
        self.message_user(request, f"{count} perfil(es) marcado(s) como no verificado(s).")


@admin.register(MobileProfile)
class MobileProfileAdmin(admin.ModelAdmin):
    list_display = ("get_username", "gender", "preferred_size", "language", "country", "created_at")
    list_filter = ("gender", "language", "country", "created_at")
    search_fields = ("user__username", "user__email", "user__dni", "preferred_size")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    @admin.display(description="Usuario")
    def get_username(self, obj):
        return obj.user.username
