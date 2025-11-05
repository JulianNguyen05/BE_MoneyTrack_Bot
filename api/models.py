from django.db import models
from django.contrib.auth.models import User
import datetime


# ==========================================================
# 💡 CATEGORY MODEL
# ==========================================================
class Category(models.Model):
    """
    Đại diện cho danh mục giao dịch.
    Ví dụ: Ăn uống, Di chuyển, Lương,...
    - type: 'expense' (chi) hoặc 'income' (thu)
    """
    TYPE_EXPENSE = "expense"
    TYPE_INCOME = "income"
    TYPE_CHOICES = [
        (TYPE_EXPENSE, "Expense"),
        (TYPE_INCOME, "Income"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["type", "name"]
        unique_together = ("user", "name", "type")  # Tránh trùng danh mục

    def __str__(self):
        emoji = "💸" if self.type == self.TYPE_EXPENSE else "💰"
        return f"{emoji} {self.name} ({self.type})"


# ==========================================================
# 💰 WALLET MODEL
# ==========================================================
class Wallet(models.Model):
    """
    Đại diện cho ví tiền của người dùng.
    Ví dụ: Tiền mặt, Ngân hàng, Momo,...
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="wallets"
    )
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"
        ordering = ["name"]
        unique_together = ("user", "name")  # Mỗi user không có 2 ví trùng tên

    def __str__(self):
        return f"{self.name} ({self.balance:,.0f}đ)"


# ==========================================================
# 💸 TRANSACTION MODEL
# ==========================================================
class Transaction(models.Model):
    """
    Đại diện cho một giao dịch (thu hoặc chi).
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transactions"
    )
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="transactions"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="transactions"
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=False)

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-date"]

    def __str__(self):
        sign = "+" if self.category.type == Category.TYPE_INCOME else "-"
        return f"{self.category.name}: {sign}{self.amount:,.0f}đ ({self.date})"

    # --- ✅ Helper: cập nhật số dư ví ---
    def apply_to_wallet(self):
        """Cộng/trừ số dư ví tương ứng với loại giao dịch."""
        if self.category.type == Category.TYPE_INCOME:
            self.wallet.balance += self.amount
        else:
            self.wallet.balance -= self.amount
        self.wallet.save()

    def revert_from_wallet(self):
        """Hoàn tác giao dịch khỏi ví (dùng khi update hoặc delete)."""
        if self.category.type == Category.TYPE_INCOME:
            self.wallet.balance -= self.amount
        else:
            self.wallet.balance += self.amount
        self.wallet.save()


# ==========================================================
# 📈 MODEL: Budget (Mới)
# ==========================================================
class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)  # Hạn mức

    # Chúng ta sẽ lưu ngân sách theo tháng/năm
    month = models.IntegerField(default=datetime.date.today().month)
    year = models.IntegerField(default=datetime.date.today().year)

    class Meta:
        # Đảm bảo mỗi user chỉ có 1 ngân sách cho 1 danh mục/tháng/năm
        unique_together = ('user', 'category', 'month', 'year')

    def __str__(self):
        return f"{self.category.name} - {self.month}/{self.year}: {self.amount}"