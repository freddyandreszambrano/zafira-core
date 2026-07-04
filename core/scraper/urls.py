from django.urls import path

from core.scraper.views import (
    ProductDeleteView,
    ProductListView,
    ScraperScanView,
    ScraperSourceCreateView,
    ScraperSourceDeleteView,
    ScraperSourceListView,
    ScraperSourceUpdateView,
)

urlpatterns = [
    path("", ScraperScanView.as_view(), name="scraper_scan"),
    path("product/", ProductListView.as_view(), name="scraper_product_list"),
    path("product/delete/<int:pk>/", ProductDeleteView.as_view(), name="scraper_product_delete"),
    path("source/", ScraperSourceListView.as_view(), name="scraper_source_list"),
    path("source/create/", ScraperSourceCreateView.as_view(), name="scraper_source_create"),
    path("source/update/<int:pk>/", ScraperSourceUpdateView.as_view(), name="scraper_source_update"),
    path("source/delete/<int:pk>/", ScraperSourceDeleteView.as_view(), name="scraper_source_delete"),
]
