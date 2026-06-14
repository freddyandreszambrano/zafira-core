from django.urls import path, include

urlpatterns = [
    path('auth/', include('core.auth.api.v1.auth.urls')),
]
