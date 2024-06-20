from django.contrib import admin
from django.urls import include, path, re_path

urlpatterns = [
    path("admin/", admin.site.urls),
    re_path(r"^", include("main.urls")),  # Assuming your main.urls uses regex.
handler404 = "main.views.custom_404_view"
