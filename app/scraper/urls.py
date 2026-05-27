from django.urls import path

from app.scraper.views import ScraperScanView


urlpatterns = [
    path('', ScraperScanView.as_view(), name='scraper_scan'),
]
