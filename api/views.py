from django.contrib.auth.models import User
from rest_framework import viewsets, permissions
from .models import Category, Wallet, Transaction
from .serializers import (
    CategorySerializer,
    WalletSerializer,
    TransactionSerializer,
    UserSerializer,
)


# --- 🔐 View: Đăng ký người dùng (Public) ---
class UserCreateView(viewsets.ModelViewSet):
    """
    Cho phép bất kỳ ai tạo tài khoản mới (đăng ký user).
    Không yêu cầu xác thực.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """Ghi đè để log dữ liệu đăng ký gửi từ Android (debug-friendly)."""
        print("\n🟢 [DEBUG] YÊU CẦU ĐĂNG KÝ MỚI ---")
        print("📥 Dữ liệu nhận được:", request.data)

        response = super().create(request, *args, **kwargs)

        print("✅ Status Code:", response.status_code)
        print("📤 Dữ liệu phản hồi:", response.data)
        print("🔚 [KẾT THÚC DEBUG]\n")

        return response


# --- ⚙️ Base ViewSet chung cho các model có trường user ---
class BaseViewSet(viewsets.ModelViewSet):
    """
    Tự động lọc dữ liệu theo user đã đăng nhập
    và gán user đó khi tạo mới bản ghi.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Chỉ lấy dữ liệu thuộc về user hiện tại."""
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Tự động gán user đang đăng nhập khi tạo mới."""
        serializer.save(user=self.request.user)


# --- 💡 Các ViewSet kế thừa từ BaseViewSet ---
class CategoryViewSet(BaseViewSet):
    """CRUD cho danh mục thu/chi."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class WalletViewSet(BaseViewSet):
    """CRUD cho ví tiền."""
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer


class TransactionViewSet(BaseViewSet):
    """CRUD cho giao dịch (thu/chi)."""
    queryset = Transaction.objects.all().order_by('-date')
    serializer_class = TransactionSerializer
