from django.urls import path

from routing.views import health, plan

urlpatterns = [
    path("api/health", health),
    path("api/plan", plan),
]
