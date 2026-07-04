from django.urls import path

from core.recommend.api.v1.recommend.views.recommend import RecommendApiView

urlpatterns = [
    path("", RecommendApiView.as_view(), name="recommend"),
]
