from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Dòng này là quan trọng nhất:
    # Nó sẽ "include" tất cả các URL từ app 'api' của bạn
    # và đặt chúng dưới tiền tố 'api/'
    path('api/', include('api.urls.main_urls')),
]