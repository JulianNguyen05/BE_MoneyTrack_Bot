from django.db import models
from django.contrib.auth.models import User
from .category import Category
import datetime


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    month = models.IntegerField(default=datetime.date.today().month)
    year = models.IntegerField(default=datetime.date.today().year)

    class Meta:
        unique_together = ('user', 'category', 'month', 'year')

    def __str__(self):
        return f"{self.category.name} - {self.month}/{self.year}: {self.amount}"
