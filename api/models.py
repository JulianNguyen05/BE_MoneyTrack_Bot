from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    """
    Đại diện cho danh mục giao dịch.
    Ví dụ: Ăn uống, Di chuyển, Lương,...
    - type: 'expense' (chi) hoặc 'income' (thu)
    """
    TYPE_CHOICES = [
        ('expense', 'Expense'),
        ('income', 'Income'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["type", "name"]

    def __str__(self):
        return f"{self.name} ({self.type})"


class Wallet(models.Model):
    """
    Đại diện cho ví tiền của người dùng.
    Ví dụ: Tiền mặt, Ngân hàng, Momo,...
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wallets")
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)

    class Meta:
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.balance:,.0f}đ)"


class Transaction(models.Model):
    """
    Đại diện cho một giao dịch (thu hoặc chi).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    date = models.DateField()

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-date"]

    def save(self, *args, **kwargs):
        """
        Ghi đè save() để cập nhật số dư ví khi tạo giao dịch mới.
        """
        is_new = self._state.adding  # True nếu đây là bản ghi mới
        if is_new:
            if self.category.type == 'income':
                self.wallet.balance += self.amount
            else:
                self.wallet.balance -= self.amount
            self.wallet.save()

        super().save(*args, **kwargs)

    def __str__(self):
        sign = "+" if self.category.type == "income" else "-"
        return f"{self.category.name}: {sign}{self.amount:,.0f}đ ({self.date})"
