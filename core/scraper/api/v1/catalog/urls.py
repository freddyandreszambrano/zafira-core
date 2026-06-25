from django.urls import path

from core.scraper.api.v1.catalog.views.product import (
    ProductDetailApiView,
    ProductListApiView,
)

urlpatterns = [
    path(
        "products/",
        ProductListApiView.as_view(),
        name="api_v1_catalog_products",
    ),
    path(
        "products/<int:pk>/",
        ProductDetailApiView.as_view(),
        name="api_v1_catalog_product_detail",
    ),
]
