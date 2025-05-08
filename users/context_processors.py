from notifications.models import Notification
from .utils import get_currency_symbol


def notification_count(request):
    if request.user.is_authenticated:
        unread_count = request.user.notifications.filter(is_read=False).count()
        return {'unread_notification_count': unread_count}
    return {'unread_notification_count': 0}


def currency_context(request):
    currency = request.session.get('currency', 'BDT')
    return {
        'selected_currency': currency,
        'currency_symbol': get_currency_symbol(currency),
    }