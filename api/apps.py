from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Cấu hình ứng dụng API — chứa các view, serializer và model chính."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
    verbose_name = "Quản lý API Ứng dụng"
