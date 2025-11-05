from django.contrib.auth.models import User
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from ..serializers import UserSerializer


class UserCreateView(viewsets.ModelViewSet):
    """Cho phép người dùng mới đăng ký tài khoản (không cần đăng nhập)."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        print("\n🟢 [DEBUG] BẮT ĐẦU ĐĂNG KÝ NGƯỜI DÙNG ---")
        print("📥 Dữ liệu nhận:", request.data)
        response = super().create(request, *args, **kwargs)
        print("✅ Mã phản hồi:", response.status_code)
        print("📤 Dữ liệu trả về:", response.data)
        print("🔚 [KẾT THÚC DEBUG]\n")
        return response
