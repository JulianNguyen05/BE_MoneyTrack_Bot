from rest_framework import viewsets, permissions


class BaseViewSet(viewsets.ModelViewSet):
    """Tự động lọc theo user đăng nhập và gán user khi tạo mới."""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return self.queryset.none()
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
