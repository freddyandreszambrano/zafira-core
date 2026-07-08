from django.core.validators import URLValidator
from django.db import models


class ScraperSource(models.Model):
    name = models.TextField(unique=True, db_index=True, verbose_name="Nombre")
    url = models.TextField(
        unique=True, db_index=True, validators=[URLValidator()], verbose_name="URL"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creacion")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualizacion")

    class Meta:
        verbose_name = "Fuente de scraper"
        verbose_name_plural = "Fuentes de scraper"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }
