from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    TYPE_EXPENSE = "expense"
    TYPE_INCOME = "income"
    TYPE_CHOICES = [
        (TYPE_EXPENSE, "Expense"),
        (TYPE_INCOME, "Income"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["type", "name"]
        unique_together = ("user", "name", "type")

    def __str__(self):
        emoji = "💸" if self.type == self.TYPE_EXPENSE else "💰"
        return f"{emoji} {self.name} ({self.type})"
