from django.urls import path

from core.scraper.views import ScraperScanView

urlpatterns = [
    path("", ScraperScanView.as_view(), name="scraper_scan"),
]
