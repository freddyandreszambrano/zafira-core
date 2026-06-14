import uuid

from django.db import models


class ExternalProvider(models.Model):
    name = models.TextField(unique=True, verbose_name="Nombre")
    client_id = models.TextField(unique=True, default=uuid.uuid4, verbose_name="Client ID")
    client_secret = models.TextField(verbose_name="Client Secret")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado")

    class Meta:
        verbose_name = "Proveedor externo"
        verbose_name_plural = "Proveedores externos"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "client_id": str(self.client_id),
            "is_active": self.is_active,
        }
