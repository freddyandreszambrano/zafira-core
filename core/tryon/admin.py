from django.contrib import admin

from core.tryon.models import TryOnJob


@admin.register(TryOnJob)
class TryOnJobAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "product__name")
    readonly_fields = ("created_at", "updated_at")
