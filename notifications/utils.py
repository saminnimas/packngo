from django.contrib.auth import get_user_model
from .models import Notification
from packages.models import Package

User = get_user_model()

def create_notification(user, notification_type, message, related_package=None):
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        message=message,
        related_package=related_package,
    )

def notify_new_package(package):
    # Notify all users about a new package
    users = User.objects.all()
    for user in users:
        message = f"New package available: {package.package_name} to {package.destination}"
        create_notification(user, 'new_package', message, related_package=package)