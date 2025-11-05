from ..models import Wallet
from ..serializers import WalletSerializer
from .base_viewset import BaseViewSet


class WalletViewSet(BaseViewSet):
    """CRUD cho ví tiền."""
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
