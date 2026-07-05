import uuid

from django.conf import settings
from django.db import models


class TryOnJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        PROCESSING = "processing", "Procesando"
        COMPLETED = "completed", "Completado"
        FAILED = "failed", "Fallido"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="try_on_jobs",
        verbose_name="Usuario",
    )
    product = models.ForeignKey(
        "scraper.Product",
        on_delete=models.CASCADE,
        related_name="try_on_jobs",
        verbose_name="Producto",
    )
    garment_image_url = models.TextField(verbose_name="Imagen de la prenda")
    garment_type = models.TextField(default="upper_body", verbose_name="Tipo de prenda")
    status = models.TextField(
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="Estado",
    )
    result_image = models.ImageField(
        upload_to="try_on_results/%Y/%m/%d/",
        null=True,
        blank=True,
        verbose_name="Resultado",
    )
    error_message = models.TextField(blank=True, verbose_name="Error")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creacion")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualizacion")

    class Meta:
        verbose_name = "Prueba virtual"
        verbose_name_plural = "Pruebas virtuales"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"TryOn {self.id} ({self.status})"

    def to_json_api(self, request=None):
        result_url = None
        if self.result_image:
            result_url = (
                request.build_absolute_uri(self.result_image.url)
                if request
                else self.result_image.url
            )
        return {
            "id": str(self.id),
            "status": self.status,
            "product_id": self.product_id,
            "result_url": result_url,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }
