from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..models import Package
from ..serializers import RecommendedPackageSerializer
from users.utils import convert_currency, get_currency_symbol
from django.contrib.auth import get_user_model
from django.db.models import Q

@api_view(['GET'])
def trending_packages(request):
    currency = request.session.get('currency', 'BDT')
    
    # Get trending packages
    trending = Package.objects.filter(
        is_trending=True,
        is_available=True
    )[:5]
    
    serializer = RecommendedPackageSerializer(trending, many=True, context={'currency': currency})
    print(f"Trending packages: {[p.package_name for p in trending]}")  # Debug
    
    response_data = {
        "trending_packages": serializer.data,
        "currency": currency,
        "currency_symbol": get_currency_symbol(currency)
    }
    return Response(response_data)