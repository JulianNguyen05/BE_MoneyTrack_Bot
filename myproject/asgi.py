"""
ASGI config for myproject.

This file exposes the ASGI callable as a module-level variable named ``application``.
It is used to serve your project via ASGI servers such as Daphne, Uvicorn, or Hypercorn.

For more information, see:
https://docs.djangoproject.com/en/stable/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

# --- Thiết lập môi trường Django ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

# --- Tạo ứng dụng ASGI ---
application = get_asgi_application()
