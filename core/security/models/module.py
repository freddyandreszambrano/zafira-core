from django.contrib.auth.models import Permission
from django.db import models


class ModuleType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    icon = models.CharField(max_length=100, blank=True, verbose_name="Icono")
    description = models.CharField(max_length=255, blank=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")

    class Meta:
        verbose_name = "Tipo de módulo"
        verbose_name_plural = "Tipos de módulos"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "is_active": self.is_active,
            "order": self.order,
        }


class Module(models.Model):
    module_type = models.ForeignKey(
        ModuleType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="modules",
        verbose_name="Tipo de módulo",
    )
    name = models.CharField(max_length=100, verbose_name="Nombre")
    url = models.CharField(max_length=255, unique=True, verbose_name="URL")
    icon = models.CharField(max_length=100, blank=True, verbose_name="Icono")
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_visible = models.BooleanField(default=True, verbose_name="Visible en menú")
    is_vertical = models.BooleanField(default=False, verbose_name="Menú vertical")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    permits = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="modules",
        verbose_name="Permisos asociados",
    )

    class Meta:
        verbose_name = "Módulo"
        verbose_name_plural = "Módulos"
        ordering = ["module_type__order", "order", "name"]
        indexes = [
            models.Index(fields=["url"]),
            models.Index(fields=["is_active", "is_visible"]),
        ]

    def __str__(self):
        return self.name

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "icon": self.icon,
            "description": self.description,
            "is_active": self.is_active,
            "is_visible": self.is_visible,
            "is_vertical": self.is_vertical,
            "module_type": self.module_type.name if self.module_type else None,
            "permissions": [p.codename for p in self.permits.all()],
        }
