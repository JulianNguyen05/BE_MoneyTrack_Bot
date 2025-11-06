from django.contrib.auth.models import User
from rest_framework import generics, permissions
from ..serializers.user_serializer import UserSerializer


class UserCreateView(generics.CreateAPIView):
    """
    API View công khai (public) để tạo tài khoản User mới.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # QUAN TRỌNG: Ghi đè cài đặt chung, cho phép bất kỳ ai
    # (kể cả chưa đăng nhập) truy cập vào view này.
    permission_classes = [permissions.AllowAny]