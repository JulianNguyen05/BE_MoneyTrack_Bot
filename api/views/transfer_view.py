from django.db import transaction
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import Wallet, Category, Transaction
from ..serializers import TransferSerializer


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
            from_wallet = Wallet.objects.get(id=data['from_wallet_id'], user=user)
            to_wallet = Wallet.objects.get(id=data['to_wallet_id'], user=user)

            if from_wallet == to_wallet:
                return Response({"error": "Ví nguồn và ví đích không được trùng nhau."},
                                status=status.HTTP_400_BAD_REQUEST)

            expense_category, _ = Category.objects.get_or_create(
                user=user, name="Chuyển tiền đi", defaults={'type': 'expense'}
            )
            income_category, _ = Category.objects.get_or_create(
                user=user, name="Nhận tiền", defaults={'type': 'income'}
            )

            with transaction.atomic():
                from_wallet.balance -= amount
                from_wallet.save(update_fields=['balance'])
                to_wallet.balance += amount
                to_wallet.save(update_fields=['balance'])

                Transaction.objects.create(
                    user=user, wallet=from_wallet, category=expense_category,
                    amount=amount, date=date, description=f"{description} (đến {to_wallet.name})"
                )
                Transaction.objects.create(
                    user=user, wallet=to_wallet, category=income_category,
                    amount=amount, date=date, description=f"{description} (từ {from_wallet.name})"
                )

            return Response({"success": "Chuyển tiền thành công."}, status=status.HTTP_200_OK)

        except Wallet.DoesNotExist:
            return Response({"error": "Không tìm thấy ví."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
