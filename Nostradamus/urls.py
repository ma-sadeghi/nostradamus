"""Project URL configuration wiring the admin and the main app."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("main.urls")),
]

handler404 = "main.views.custom_404_view"
