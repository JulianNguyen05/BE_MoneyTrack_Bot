import datetime
from datetime import timedelta
from django.db.models import Sum, Q, DecimalField, Value
from django.db.models.functions import Coalesce
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import Transaction


class CashFlowReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        today = datetime.date.today()

        try:
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else today - timedelta(days=30)
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else today
        except (ValueError, TypeError):
            start_date = today - timedelta(days=30)
            end_date = today

        daily_summary_query = Transaction.objects.filter(
            user=user,
            date__range=[start_date, end_date]
        ).values('date').annotate(
            total_income=Coalesce(
                Sum('amount', filter=Q(category__type='income'), output_field=DecimalField()),
                Value(0, output_field=DecimalField())
            ),
            total_expense=Coalesce(
                Sum('amount', filter=Q(category__type='expense'), output_field=DecimalField()),
                Value(0, output_field=DecimalField())
            )
        ).order_by('date')

        daily_summary_data = [
            {'day': item['date'], 'total_income': item['total_income'], 'total_expense': item['total_expense']}
            for item in daily_summary_query
        ]

        return Response(daily_summary_data, status=status.HTTP_200_OK)
