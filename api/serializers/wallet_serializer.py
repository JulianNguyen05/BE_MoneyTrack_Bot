from rest_framework import serializers
from ..models import Wallet


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
