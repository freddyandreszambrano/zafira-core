from django.contrib import admin

from .models import ExternalProvider, Group, GroupModule, GroupPermission, Module, ModuleType


@admin.register(ModuleType)
class ModuleTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    ordering = ("order", "name")


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "module_type", "order", "is_active", "is_visible", "is_vertical")
    list_filter = ("module_type", "is_active", "is_visible", "is_vertical")
    search_fields = ("name", "url", "description")
    ordering = ("module_type__order", "order", "name")
    filter_horizontal = ("permits",)


class GroupModuleInline(admin.TabularInline):
    model = GroupModule
    extra = 1


class GroupPermissionInline(admin.TabularInline):
    model = GroupPermission
    extra = 1


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    inlines = [GroupModuleInline, GroupPermissionInline]


@admin.register(GroupModule)
class GroupModuleAdmin(admin.ModelAdmin):
    list_display = ("group", "module")
    list_filter = ("group",)
    search_fields = ("group__name", "module__name")


@admin.register(GroupPermission)
class GroupPermissionAdmin(admin.ModelAdmin):
    list_display = ("group", "module", "permission")
    list_filter = ("group", "module")
    search_fields = ("group__name", "module__name", "permission__codename")


@admin.register(ExternalProvider)
class ExternalProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "client_id", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "client_id")
    ordering = ("name",)
