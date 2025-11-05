from rest_framework import serializers
from ..models import Category


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer cho danh mục giao dịch (thu/chi).
    """
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ('user',)
