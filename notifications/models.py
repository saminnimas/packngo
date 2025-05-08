from django.db import models
from django.conf import settings
from packages.models import Package
from django.utils import timezone


# Create your models here.
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('expense_alert', 'Expense Alert'),
        ('package_confirmation', 'Package Confirmation'),
        ('new_package', 'New Package Arrival'),
        ('profile_update', 'Profile Update'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    package = models.ForeignKey(Package, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} for {self.user.username}: {self.message}"