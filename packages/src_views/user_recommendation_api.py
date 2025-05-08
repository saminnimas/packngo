from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..models import Package
from ..serializers import RecommendedPackageSerializer
from users.utils import convert_currency, get_currency_symbol
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

@api_view(['GET'])
def user_recommended_packages(request):
    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    currency = request.session.get('currency', 'BDT')
    user = request.user
    recommendations = {
        "purchased_destinations": [],
        "expense_threshold": []
    }

    try:
        # 1. Recommendations based on purchased destinations
        purchased_destinations = Package.objects.filter(
            payments__user=user,  # Changed from payment_set to payments
            payments__status='succeeded',
            is_available=True
        ).values('destination').distinct()
        print(f"Purchased destinations: {[d['destination'] for d in purchased_destinations]}")  # Debug
        destination_based = Package.objects.filter(
            destination__in=[d['destination'] for d in purchased_destinations],
            is_available=True
        ).exclude(
            id__in=[p.package.id for p in user.payment_set.filter(status='succeeded')]  # Keep payment_set for CustomUser
        )[:3]
        destination_serializer = RecommendedPackageSerializer(destination_based, many=True, context={'currency': currency})
        recommendations['purchased_destinations'] = destination_serializer.data
        print(f"Purchased destinations recommendations: {[p.package_name for p in destination_based]}")  # Debug

        # 2. Recommendations based on expense threshold
        threshold_based = Package.objects.filter(
            price__lte=user.expense_threshold,
            is_available=True
        ).exclude(
            id__in=[p.package.id for p in user.payment_set.filter(status='succeeded')]  # Keep payment_set for CustomUser
        )[:3]
        threshold_serializer = RecommendedPackageSerializer(threshold_based, many=True, context={'currency': currency})
        recommendations['expense_threshold'] = threshold_serializer.data
        print(f"Expense threshold recommendations: {[p.package_name for p in threshold_based]}")  # Debug

        response_data = {
            "recommendations": recommendations,
            "currency": currency,
            "currency_symbol": get_currency_symbol(currency)
        }
        return Response(response_data)

    except Exception as e:
        print(f"Error in user_recommended_packages: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)