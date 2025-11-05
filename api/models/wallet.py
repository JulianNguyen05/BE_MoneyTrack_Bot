from django.db import models
from django.contrib.auth.models import User


class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wallets")
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"
        ordering = ["name"]
        unique_together = ("user", "name")

    def __str__(self):
        return f"{self.name} ({self.balance:,.0f}đ)"
