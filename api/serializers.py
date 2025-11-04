from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Category, Wallet, Transaction


# ==========================================================
# 👤 User Serializer
# ==========================================================
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer cho đăng ký tài khoản người dùng mới.
    """
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('id', 'username', 'password')

    def create(self, validated_data):
        """
        Tạo user mới với mật khẩu được mã hóa.
        """
        return User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )


# ==========================================================
# 🗂 Category Serializer
# ==========================================================
class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer cho danh mục giao dịch (thu/chi).
    """
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ('user',)


# ==========================================================
# 💰 Wallet Serializer
# ==========================================================
class WalletSerializer(serializers.ModelSerializer):
    """
    Serializer cho ví tiền của người dùng.
    """
    formatted_balance = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = '__all__'
        read_only_fields = ('user',)

    def get_formatted_balance(self, obj):
        """
        Hiển thị số dư định dạng dễ đọc, ví dụ: 1,200,000đ
        """
        return f"{obj.balance:,.0f}đ"


# ==========================================================
# 📊 Transaction Serializer
# ==========================================================
class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer cho giao dịch thu/chi.
    - Hiển thị tên danh mục, ví và kiểu danh mục
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    wallet_name = serializers.CharField(source='wallet.name', read_only=True)
    category_type = serializers.CharField(source='category.get_type_display', read_only=True)

    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('user',)


# ==========================================================
# 🔄 Transfer Serializer (Không dùng Model)
# ==========================================================
class TransferSerializer(serializers.Serializer):
    """
    Serializer không liên kết với model.
    Dùng để xác thực dữ liệu đầu vào cho API chuyển tiền giữa các ví.
    """
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    from_wallet_id = serializers.IntegerField()
    to_wallet_id = serializers.IntegerField()
    date = serializers.DateField()
    description = serializers.CharField(required=False, allow_blank=True, max_length=200)
