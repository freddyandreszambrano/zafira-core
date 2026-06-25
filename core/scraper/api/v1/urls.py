from django.urls import include, path

urlpatterns = [
    path("catalog/", include("core.scraper.api.v1.catalog.urls")),
]
