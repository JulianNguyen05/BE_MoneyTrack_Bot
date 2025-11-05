from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views


# ==========================================================
# 🚀 Router tự động sinh CRUD endpoints
# ==========================================================
router = DefaultRouter()
router.register(r'users', views.UserCreateView, basename='user')          # POST /api/users/ → đăng ký
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'wallets', views.WalletViewSet, basename='wallet')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'budgets', views.BudgetViewSet, basename='budget')


# ==========================================================
# 🌐 URL Patterns
# ==========================================================
urlpatterns = [
    # --- CRUD routes ---
    path('', include(router.urls)),

    # --- JWT Authentication ---
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),     # Đăng nhập: trả về access + refresh token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),    # Làm mới token

    # --- 💸 API chuyển tiền giữa ví ---
    path('transfer/', views.TransferView.as_view(), name='transfer'),

    # --- 📊 Báo cáo tổng hợp giao dịch ---
    path('reports/summary/', views.ReportView.as_view(), name='report-summary'),
]
