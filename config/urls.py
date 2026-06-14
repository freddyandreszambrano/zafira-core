from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("core.auth.api.v1.urls")),
    path("api/v1/", include("core.user.api.v1.urls")),
    path("", include("core.profiles.urls")),
    path("", include("core.user.urls")),
    path("security/", include("core.security.urls")),
    path("scraper/", include("core.scraper.urls")),
    path("", include("core.auth.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
