from django.db import models


class Product(models.Model):
    id_external = models.TextField(unique=True, db_index=True, verbose_name="ID externo")
    name = models.TextField(verbose_name="Nombre")
    category = models.TextField(db_index=True, verbose_name="Categoria original")
    gender = models.TextField(db_index=True, blank=True, verbose_name="Genero")
    url = models.URLField(max_length=500, verbose_name="URL")
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

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Product: {self.name} ({self.id_external})>"
