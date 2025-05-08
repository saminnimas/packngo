from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..models import Package
from ..serializers import PackageSerializer, RecommendedPackageSerializer
from users.utils import convert_currency, get_currency_symbol
from decimal import Decimal


@api_view(['GET'])
def package_detail_api(request, pk):
    print(f"API called for package ID: {pk}")  # Debug
    try:
        package = Package.objects.get(pk=pk, is_available=True)
        print(f"Found package: {package.package_name}, Price: {package.price}, Destination: {package.destination}")  # Debug
    except Package.DoesNotExist:
        print(f"Package {pk} not found or unavailable")  # Debug
        return Response({"error": "Package not found or unavailable"}, status=status.HTTP_404_NOT_FOUND)

    currency = request.session.get('currency', 'BDT')
    print(f"Currency: {currency}")  # Debug
    
    package_serializer = PackageSerializer(package, context={'currency': currency})
    
    # Recommendation logic
    recommended = []
    
    # 1. Price range (±20% of current package price)
    price = Decimal(str(package.price))
    price_min = price * Decimal('0.8')  # -20%
    price_max = price * Decimal('1.2')  # +20%
    price_based = Package.objects.filter(
        price__gte=price_min,
        price__lte=price_max,
        is_available=True
    ).exclude(id=package.id)[:3]
    recommended.extend(price_based)
    print(f"Price-based recommendations: {[p.package_name for p in price_based]}")  # Debug
    
    # 2. Same destination (if fewer than 3 recommendations)
    if len(recommended) < 3:
        destination_based = Package.objects.filter(
            destination=package.destination,
            is_available=True
        ).exclude(id=package.id).exclude(id__in=[p.id for p in recommended])[:3 - len(recommended)]
        recommended.extend(destination_based)
        print(f"Destination-based recommendations: {[p.package_name for p in destination_based]}")  # Debug
    
    # 3. Trending packages
    if len(recommended) < 3:
        trending = Package.objects.filter(
            is_trending=True,
            is_available=True
        ).exclude(id=package.id).exclude(id__in=[p.id for p in recommended])[:3 - len(recommended)]
        recommended.extend(trending)
        print(f"Trending recommendations: {[p.package_name for p in trending]}")  # Debug
    
    recommended_serializer = RecommendedPackageSerializer(recommended, many=True, context={'currency': currency})
    
    response_data = {
        "package": package_serializer.data,
        "recommended_packages": recommended_serializer.data,
        "currency": currency,
        "currency_symbol": get_currency_symbol(currency)
    }
    return Response(response_data)