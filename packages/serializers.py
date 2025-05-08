from rest_framework import serializers
from .models import Package
from users.utils import convert_currency, get_currency_symbol

class PackageSerializer(serializers.ModelSerializer):
    converted_price = serializers.SerializerMethodField()
    currency_symbol = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = ['id', 'package_name', 'destination', 'description', 'price', 'converted_price', 'currency_symbol', 'image', 'start_date', 'end_date']

    def get_converted_price(self, obj):
        currency = self.context.get('currency', 'BDT')
        return convert_currency(obj.price, to_currency=currency)

    def get_currency_symbol(self, obj):
        currency = self.context.get('currency', 'BDT')
        return get_currency_symbol(currency)

class RecommendedPackageSerializer(serializers.ModelSerializer):
    converted_price = serializers.SerializerMethodField()
    currency_symbol = serializers.SerializerMethodField()
    image = serializers.ImageField(allow_null=True)

    class Meta:
        model = Package
        fields = ['id', 'package_name', 'destination', 'converted_price', 'currency_symbol', 'image']

    def get_converted_price(self, obj):
        currency = self.context.get('currency', 'BDT')
        return convert_currency(obj.price, to_currency=currency)

    def get_currency_symbol(self, obj):
        currency = self.context.get('currency', 'BDT')
        return get_currency_symbol(currency)