import datetime
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import Transaction


class ReportView(APIView):
    """Tổng hợp chi tiêu theo danh mục trong khoảng thời gian."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        try:
            if request.query_params.get('start_date'):
                start_date = datetime.datetime.strptime(request.query_params.get('start_date'), '%Y-%m-%d').date()
            if request.query_params.get('end_date'):
                end_date = datetime.datetime.strptime(request.query_params.get('end_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass

        expenses = (
            Transaction.objects.filter(
                user=user, category__type='expense', date__range=[start_date, end_date]
            )
            .values('category__name')
            .annotate(total_amount=Sum('amount'))
            .order_by('-total_amount')
        )

        return Response(expenses, status=status.HTTP_200_OK)
