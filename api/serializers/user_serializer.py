from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer cho đăng ký tài khoản người dùng mới.
    """
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('id', 'username', 'password')

    def create(self, validated_data):
        """
        Tạo user mới với mật khẩu được mã hóa.
        """
        return User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
