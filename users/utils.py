from decimal import Decimal

# Static exchange rates (BDT to other currencies, approximate as of May 2025)
EXCHANGE_RATES = {
    'BDT': Decimal('1.0'),    # Base currency
    'USD': Decimal('0.0083'), # 1 BDT = 0.0083 USD
    'EUR': Decimal('0.0077'), # 1 BDT = 0.0077 EUR
    'SAR': Decimal('0.0312'), # 1 BDT = 0.0312 SAR
    'JPY': Decimal('1.25'),   # 1 BDT = 1.25 JPY
}

CURRENCY_SYMBOLS = {
    'BDT': '৳',
    'USD': '$',
    'EUR': '€',
    'SAR': '﷼',
    'JPY': '¥',
}

def convert_currency(amount, from_currency='BDT', to_currency='BDT'):
    """Convert an amount from one currency to another."""
    if from_currency not in EXCHANGE_RATES or to_currency not in EXCHANGE_RATES:
        return amount
    # Ensure amount is Decimal
    amount = Decimal(str(amount)) if not isinstance(amount, Decimal) else amount
    # Convert to BDT first if not already in BDT
    amount_in_bdt = amount if from_currency == 'BDT' else amount / EXCHANGE_RATES[from_currency]
    # Convert from BDT to target currency
    converted_amount = amount_in_bdt * EXCHANGE_RATES[to_currency]
    return round(converted_amount, 2)

def get_currency_symbol(currency):
    """Return the symbol for the given currency."""
    return CURRENCY_SYMBOLS.get(currency, '৳')