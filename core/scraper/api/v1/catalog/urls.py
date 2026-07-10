from django.urls import path

from core.scraper.api.v1.catalog.views.favorite import (
    FavoriteDetailApiView,
    FavoriteListApiView,
    FavoriteOutfitDetailApiView,
    FavoriteOutfitListApiView,
)
from core.scraper.api.v1.catalog.views.product import (
    ProductDetailApiView,
    ProductListApiView,
    ProductLiveApiView,
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
        "products/<int:pk>/live/",
        ProductLiveApiView.as_view(),
        name="api_v1_catalog_product_live",
    ),
    path(
        "favorites/",
        FavoriteListApiView.as_view(),
        name="api_v1_catalog_favorites",
    ),
    path(
        "favorites/outfits/",
        FavoriteOutfitListApiView.as_view(),
        name="api_v1_catalog_favorite_outfits",
    ),
    path(
        "favorites/outfits/<int:outfit_id>/",
        FavoriteOutfitDetailApiView.as_view(),
        name="api_v1_catalog_favorite_outfit_detail",
    ),
    path(
        "favorites/<int:product_id>/",
        FavoriteDetailApiView.as_view(),
        name="api_v1_catalog_favorite_detail",
    ),
]
