from django.db import models


class Product(models.Model):
    id_external = models.TextField(db_index=True, verbose_name="ID externo")
    name = models.TextField(verbose_name="Nombre")
    category = models.TextField(db_index=True, verbose_name="Categoria original")
    gender = models.TextField(db_index=True, blank=True, verbose_name="Genero")
    url = models.TextField(verbose_name="URL")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    price_old = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio anterior"
    )
    currency = models.TextField(default="USD", verbose_name="Moneda")
    sizes = models.JSONField(default=list, blank=True, verbose_name="Tallas")
    colors = models.JSONField(default=list, blank=True, verbose_name="Colores")
    description = models.TextField(blank=True, verbose_name="Descripcion")
    image_urls = models.JSONField(default=list, blank=True, verbose_name="Imagenes")
    availability = models.TextField(default="unknown", verbose_name="Disponibilidad")
    store = models.TextField(default="modarm", db_index=True, verbose_name="Tienda")
    base_name = models.TextField(db_index=True, blank=True, verbose_name="Nombre base (sin color)")
    extracted_at = models.DateTimeField(verbose_name="Fecha de extraccion")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creacion")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualizacion")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["-extracted_at"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["gender"]),
            models.Index(fields=["store"]),
            models.Index(fields=["base_name"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["store", "id_external"],
                name="scraper_product_store_idext_uniq",
            )
        ]

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Product: {self.name} ({self.id_external})>"

    def to_json(self):
        return {
            "id": self.id,
            "id_external": self.id_external,
            "store": self.store,
            "name": self.name,
            "base_name": self.base_name,
            "category": self.category,
            "gender": self.gender,
            "url": self.url,
            "price": str(self.price),
            "price_old": str(self.price_old) if self.price_old is not None else None,
            "currency": self.currency,
            "sizes": self.sizes,
            "colors": self.colors,
            "availability": self.availability,
            "image_urls": self.image_urls,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else "",
        }

    def to_json_api(self, request=None):
        return {
            "id": self.id,
            "id_external": self.id_external,
            "name": self.name,
            "category": self.category,
            "gender": self.gender,
            "url": self.url,
            "price": str(self.price),
            "price_old": str(self.price_old) if self.price_old is not None else None,
            "currency": self.currency,
            "sizes": self.sizes,
            "colors": self.colors,
            "description": self.description,
            "image_urls": self.image_urls,
            "availability": self.availability,
            "store": self.store,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else "",
            "color_options": self.get_color_options_api(),
            "is_favorite": self.is_favorite_for_request(request),
        }

    def get_color_options_api(self):
        if not self.base_name:
            return []

        siblings = (
            Product.objects.filter(
                base_name=self.base_name,
                category=self.category,
                gender=self.gender,
            )
            .exclude(pk=self.pk)
            .order_by("name")
        )

        return [
            {
                "id": sibling.id,
                "color": sibling.colors[0] if sibling.colors else None,
                "image_url": sibling.image_urls[0] if sibling.image_urls else None,
            }
            for sibling in siblings
        ]

    def is_favorite_for_request(self, request=None):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        from .favorite import Favorite

        return Favorite.objects.filter(user=user, product=self).exists()
