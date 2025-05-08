from django import template
from users.utils import get_currency_symbol

register = template.Library()

@register.filter
def get_currency_symbol(value):
    return get_currency_symbol(value)