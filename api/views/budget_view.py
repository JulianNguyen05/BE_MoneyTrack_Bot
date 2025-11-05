import datetime
from ..models import Budget
from ..serializers import BudgetSerializer
from .base_viewset import BaseViewSet


class BudgetViewSet(BaseViewSet):
    """CRUD cho Ngân sách (Budgets)."""
    queryset = Budget.objects.all().order_by('category__name')
    serializer_class = BudgetSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        today = datetime.date.today()
        month = self.request.query_params.get('month', today.month)
        year = self.request.query_params.get('year', today.year)
        return queryset.filter(month=month, year=year)
