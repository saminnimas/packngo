from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.
class CustomUser(AbstractUser):
    phone = PhoneNumberField(blank=True, null=True)
    expense_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=100000.00, help_text="Threshold for expense alerts in BDT")
    purchase_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.username


class TestUsers(models.Model):
    name = models.CharField(max_length=80)
    age = models.IntegerField()
