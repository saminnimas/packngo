from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Notification
# from packages.models import Package
from django.urls import reverse


# Create your views here.
@login_required
def notifications_list(request):
    """Display all notifications for the logged-in user."""
    notifications = request.user.notifications.all()
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/notifications_list.html', {'notifications': notifications})

@login_required
def notification_redirect(request, notification_id):
    """Redirect to appropriate page based on notification type."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()

    if notification.notification_type in ['expense_alert', 'password_change']:
        return redirect('profile')
    elif notification.notification_type == 'package_confirmation' and notification.package:
        return redirect('package_detail', package_id=notification.package.id)
    elif notification.notification_type == 'new_package' and notification.package:
        return redirect('package_detail', package_id=notification.package.id)
    return redirect('notifications_list')