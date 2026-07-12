from django.conf import settings
from django.db import models

from .product import Product


class FavoriteOutfit(models.Model):
    """Outfit completo (torso + pierna) guardado por el usuario, junto con la
    imagen ya generada por el probador para no regenerar al verlo."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_outfits",
        verbose_name="Usuario",
    )
    top = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="outfit_tops",
        verbose_name="Prenda de arriba",
    )
    bottom = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="outfit_bottoms",
        verbose_name="Prenda de abajo",
    )
    result_image_url = models.TextField(
        blank=True, default="", verbose_name="Imagen generada del try-on"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creacion")

    class Meta:
        verbose_name = "Outfit favorito"
        verbose_name_plural = "Outfits favoritos"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "top", "bottom"], name="unique_user_outfit_favorite"
            ),
        ]

    def __str__(self):
        return f"{self.user} -> {self.top} + {self.bottom}"

    def to_json_api(self, request=None):
        return {
            "id": self.id,
            "top": self.top.to_json_api(request=request),
            "bottom": self.bottom.to_json_api(request=request),
            "result_image_url": self.result_image_url,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Usuario",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name="Producto",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creacion")

    class Meta:
        verbose_name = "Favorito"
        verbose_name_plural = "Favoritos"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"], name="unique_user_product_favorite"
            ),
        ]

    def __str__(self):
        return f"{self.user} -> {self.product}"
