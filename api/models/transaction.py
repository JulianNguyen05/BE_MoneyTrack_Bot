from django.db import models
from django.contrib.auth.models import User
from .wallet import Wallet
from .category import Category


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="transactions")
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

    # --- Cập nhật số dư ví ---
    def apply_to_wallet(self):
        if self.category.type == Category.TYPE_INCOME:
            self.wallet.balance += self.amount
        else:
            self.wallet.balance -= self.amount
        self.wallet.save()

    def revert_from_wallet(self):
        if self.category.type == Category.TYPE_INCOME:
            self.wallet.balance -= self.amount
        else:
            self.wallet.balance += self.amount
        self.wallet.save()
