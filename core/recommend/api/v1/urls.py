from django.urls import include, path

urlpatterns = [
    path("recommend/", include("core.recommend.api.v1.recommend.urls")),
]
