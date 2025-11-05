from ..models import Category
from ..serializers import CategorySerializer
from .base_viewset import BaseViewSet


class CategoryViewSet(BaseViewSet):
    """CRUD cho danh mục thu/chi."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
