from django.contrib.auth.models import User
from rest_framework import viewsets, permissions
from .models import Category, Wallet, Transaction
from .serializers import (
    CategorySerializer,
    WalletSerializer,
    TransactionSerializer,
    UserSerializer,
)

# ==========================================================
# 🔐 Đăng ký người dùng (Public)
# ==========================================================
class UserCreateView(viewsets.ModelViewSet):
    """
    Cho phép người dùng mới đăng ký tài khoản.
    Không yêu cầu đăng nhập.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        print("\n🟢 [DEBUG] BẮT ĐẦU ĐĂNG KÝ NGƯỜI DÙNG ---")
        print("📥 Dữ liệu nhận:", request.data)

        response = super().create(request, *args, **kwargs)

        print("✅ Mã phản hồi:", response.status_code)
        print("📤 Dữ liệu trả về:", response.data)
        print("🔚 [KẾT THÚC DEBUG]\n")

        return response


# ==========================================================
# ⚙️ Base ViewSet chung cho model có trường user
# ==========================================================
class BaseViewSet(viewsets.ModelViewSet):
    """
    Tự động lọc dữ liệu theo user đăng nhập.
    Gán user đó khi tạo mới bản ghi.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Chỉ lấy dữ liệu của user hiện tại."""
        if not self.request.user.is_authenticated:
            return self.queryset.none()
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Tự động gán user đăng nhập."""
        serializer.save(user=self.request.user)


# ==========================================================
# 💡 CRUD: Category
# ==========================================================
class CategoryViewSet(BaseViewSet):
    """CRUD cho danh mục thu/chi."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# ==========================================================
# 💰 CRUD: Wallet
# ==========================================================
class WalletViewSet(BaseViewSet):
    """CRUD cho ví tiền."""
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer


# ==========================================================
# 💸 CRUD: Transaction (cập nhật số dư ví)
# ==========================================================
class TransactionViewSet(BaseViewSet):
    """CRUD cho giao dịch và tự động cập nhật số dư ví."""
    queryset = Transaction.objects.all().order_by('-date')
    serializer_class = TransactionSerializer

    # --- 🟢 Khi tạo giao dịch ---
    def perform_create(self, serializer):
        transaction = serializer.save(user=self.request.user)
        wallet = transaction.wallet

        if transaction.category.type == 'income':
            wallet.balance += transaction.amount
        else:  # expense
            wallet.balance -= transaction.amount
        wallet.save()

    # --- 🟠 Khi cập nhật giao dịch ---
    def perform_update(self, serializer):
        old_transaction = self.get_object()
        old_wallet = old_transaction.wallet
        old_amount = old_transaction.amount
        old_type = old_transaction.category.type

        # Hoàn tác số dư cũ
        if old_type == 'income':
            old_wallet.balance -= old_amount
        else:
            old_wallet.balance += old_amount
        old_wallet.save()

        # Lưu giao dịch mới
        new_transaction = serializer.save()
        new_wallet = new_transaction.wallet

        if old_wallet.id == new_wallet.id:
            new_wallet.refresh_from_db()

        if new_transaction.category.type == 'income':
            new_wallet.balance += new_transaction.amount
        else:
            new_wallet.balance -= new_transaction.amount
        new_wallet.save()

    # --- 🔴 Khi xóa giao dịch ---
    def perform_destroy(self, instance):
        wallet = instance.wallet

        if instance.category.type == 'income':
            wallet.balance -= instance.amount
        else:
            wallet.balance += instance.amount
        wallet.save()

        instance.delete()
