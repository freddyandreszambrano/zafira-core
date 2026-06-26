from django.urls import path

from core.scraper.api.v1.catalog.views.favorite import (
    FavoriteDetailApiView,
    FavoriteListApiView,
)
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
    path(
        "favorites/",
        FavoriteListApiView.as_view(),
        name="api_v1_catalog_favorites",
    ),
    path(
        "favorites/<int:product_id>/",
        FavoriteDetailApiView.as_view(),
        name="api_v1_catalog_favorite_detail",
    ),
]
