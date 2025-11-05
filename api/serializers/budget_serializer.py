from rest_framework import serializers
from ..models import Budget
from .category_serializer import CategorySerializer


class BudgetSerializer(serializers.ModelSerializer):
    """
    Serializer cho ngân sách người dùng theo tháng/năm.
    """
    category_details = CategorySerializer(source='category', read_only=True)

    class Meta:
        model = Budget
        fields = ('id', 'category', 'amount', 'month', 'year', 'category_details')
        read_only_fields = ('user', 'category_details')
