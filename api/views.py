from datetime import timedelta
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Category, Wallet, Transaction
from .serializers import (
    CategorySerializer,
    WalletSerializer,
    TransactionSerializer,
    UserSerializer,
    TransferSerializer,
)


# ==========================================================
# 🔐 Đăng ký người dùng (Public)
# ==========================================================
class UserCreateView(viewsets.ModelViewSet):
    """Cho phép người dùng mới đăng ký tài khoản (không cần đăng nhập)."""
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
    """Tự động lọc theo user đăng nhập và gán user khi tạo mới."""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return self.queryset.none()
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
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
# 💸 CRUD: Transaction (Cập nhật số dư ví)
# ==========================================================
class TransactionViewSet(BaseViewSet):
    """CRUD cho giao dịch và tự động cập nhật số dư ví."""
    queryset = Transaction.objects.all().order_by('-date')
    serializer_class = TransactionSerializer

    def perform_create(self, serializer):
        """Tạo giao dịch mới và cập nhật số dư ví."""
        transaction_obj = serializer.save(user=self.request.user)
        wallet = transaction_obj.wallet

        if transaction_obj.category.type == 'income':
            wallet.balance += transaction_obj.amount
        else:
            wallet.balance -= transaction_obj.amount

        wallet.save(update_fields=['balance'])

    def perform_update(self, serializer):
        """Cập nhật giao dịch và điều chỉnh số dư ví."""
        old_transaction = self.get_object()
        old_wallet = old_transaction.wallet
        old_amount = old_transaction.amount
        old_type = old_transaction.category.type

        # 1️⃣ Hoàn tác số dư cũ
        if old_type == 'income':
            old_wallet.balance -= old_amount
        else:
            old_wallet.balance += old_amount
        old_wallet.save(update_fields=['balance'])

        # 2️⃣ Lưu giao dịch mới
        new_transaction = serializer.save()
        new_wallet = new_transaction.wallet

        # 3️⃣ Nếu đổi ví, đảm bảo ví mới được cập nhật chính xác
        if old_wallet.id != new_wallet.id:
            new_wallet.refresh_from_db()

        # 4️⃣ Cập nhật số dư ví mới
        if new_transaction.category.type == 'income':
            new_wallet.balance += new_transaction.amount
        else:
            new_wallet.balance -= new_transaction.amount
        new_wallet.save(update_fields=['balance'])

    def perform_destroy(self, instance):
        """Xóa giao dịch và hoàn tác số dư ví."""
        wallet = instance.wallet

        if instance.category.type == 'income':
            wallet.balance -= instance.amount
        else:
            wallet.balance += instance.amount

        wallet.save(update_fields=['balance'])
        instance.delete()


# ==========================================================
# 🏦 API: Chuyển tiền giữa 2 ví
# ==========================================================
class TransferView(APIView):
    """API chuyển tiền giữa 2 ví của cùng 1 user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        amount = data['amount']
        date = data['date']
        description = data.get('description', 'Chuyển tiền')

        try:
            # 1️⃣ Lấy ví nguồn & đích
            from_wallet = Wallet.objects.get(id=data['from_wallet_id'], user=user)
            to_wallet = Wallet.objects.get(id=data['to_wallet_id'], user=user)

            if from_wallet == to_wallet:
                return Response(
                    {"error": "Ví nguồn và ví đích không được trùng nhau."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if from_wallet.balance < amount:
                return Response(
                    {"error": "Số dư ví nguồn không đủ để chuyển."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2️⃣ Danh mục mặc định
            expense_category, _ = Category.objects.get_or_create(
                user=user,
                name="Chuyển tiền đi",
                defaults={'type': 'expense'}
            )
            income_category, _ = Category.objects.get_or_create(
                user=user,
                name="Nhận tiền",
                defaults={'type': 'income'}
            )

            # 3️⃣ Giao dịch an toàn
            with transaction.atomic():
                from_wallet.balance -= amount
                from_wallet.save(update_fields=['balance'])

                to_wallet.balance += amount
                to_wallet.save(update_fields=['balance'])

                Transaction.objects.create(
                    user=user,
                    wallet=from_wallet,
                    category=expense_category,
                    amount=amount,
                    date=date,
                    description=f"{description} (đến {to_wallet.name})"
                )
                Transaction.objects.create(
                    user=user,
                    wallet=to_wallet,
                    category=income_category,
                    amount=amount,
                    date=date,
                    description=f"{description} (từ {from_wallet.name})"
                )

            return Response({"success": "Chuyển tiền thành công."}, status=status.HTTP_200_OK)

        except Wallet.DoesNotExist:
            return Response({"error": "Không tìm thấy ví."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================================
# 📊 API Báo cáo chi tiêu theo danh mục
# ==========================================================
class ReportView(APIView):
    """Tổng hợp chi tiêu theo danh mục trong khoảng thời gian."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # 1️⃣ Khoảng thời gian mặc định: 30 ngày qua
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        # 2️⃣ Cho phép truyền query params
        if request.query_params.get('start_date'):
            start_date = request.query_params.get('start_date')
        if request.query_params.get('end_date'):
            end_date = request.query_params.get('end_date')

        # 3️⃣ Tổng hợp chi tiêu theo danh mục
        expenses = (
            Transaction.objects.filter(
                user=user,
                category__type='expense',
                date__range=[start_date, end_date]
            )
            .values('category__name')
            .annotate(total_amount=Sum('amount'))
            .order_by('-total_amount')
        )

        return Response(expenses, status=status.HTTP_200_OK)
