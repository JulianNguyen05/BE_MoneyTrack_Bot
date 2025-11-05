from rest_framework import serializers
from ..models import Transaction


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
