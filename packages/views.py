from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import (Package,
                     Hotels,
                     HotelRoom, 
                     Booking, 
                     CustomPackage, 
                     Payment,
                     Voucher)
from notifications.models import Notification
from .serializers import PackageSerializer, RecommendedPackageSerializer
from .forms import (CustomPackageForm,
                    PackageForm,
                    ReviewForm)
from .src_views import (hotel_booking, 
                        flight_booking, 
                        get_flight_price, 
                        expense_log, 
                        expense_log_visualization, 
                        package_detail_api,
                        user_recommended_packages,
                        trending_packages)
from users.utils import convert_currency, get_currency_symbol

import stripe
import requests
from datetime import datetime, timedelta
from notifications.utils import create_notification
from decimal import Decimal


# amadeus = Client(client_id=settings.AMADEUS_API_KEY, client_secret=settings.AMADEUS_API_SECRET)
stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.
def package_list(request):
    packages = Package.objects.filter(is_available=True)

    # Search by destination
    destination = request.GET.get('destination', '').strip()
    if destination:
        packages = packages.filter(
            Q(description__icontains=destination) |
            Q(custom_components__destination__icontains=destination) |
            Q(custom_components__hotel_destination__icontains=destination)
        )

    # Filter by price range
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    if price_min:
        packages = packages.filter(price__gte=float(price_min))
    if price_max:
        packages = packages.filter(price__lte=float(price_max))

    # Filter by availability dates
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')
    if check_in:
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        packages = packages.filter(start_date__gte=check_in_date)
    if check_out:
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        packages = packages.filter(end_date__lte=check_out_date)

    # Filter by duration
    duration = request.GET.get('duration')
    if duration:
        if duration == '0-3':
            packages = packages.filter(
                start_date__isnull=False,
                end_date__isnull=False
            ).extra(
                where=["(end_date - start_date) <= 3"]
            )
        elif duration == '3-5':
            packages = packages.filter(
                start_date__isnull=False,
                end_date__isnull=False
            ).extra(
                where=["(end_date - start_date) > 3 AND (end_date - start_date) <= 5"]
            )
        elif duration == '5-7':
            packages = packages.filter(
                start_date__isnull=False,
                end_date__isnull=False
            ).extra(
                where=["(end_date - start_date) > 5 AND (end_date - start_date) <= 7"]
            )
        elif duration == '7+':
            packages = packages.filter(
                start_date__isnull=False,
                end_date__isnull=False
            ).extra(
                where=["(end_date - start_date) > 7"]
            )

    paginator = Paginator(packages, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    all_packages = Package.objects.filter(is_available=True)
    destinations = set()
    for pkg in all_packages:
        if pkg.custom_components:
            if 'destination' in pkg.custom_components:
                destinations.add(pkg.custom_components['destination'])
            if 'hotel_destination' in pkg.custom_components:
                destinations.add(pkg.custom_components['hotel_destination'])

    return render(request, 'packages/package_list.html', {
        'page_obj': page_obj,
        'destination': destination,
        'destinations': sorted(destinations),
        'price_min': price_min if price_min else 0,
        'price_max': price_max if price_max else 100000,  # Adjust max as needed
        'check_in': check_in,
        'check_out': check_out,
        'duration': duration,
    })


def package_detail(request, package_id):
    package = get_object_or_404(Package, id=package_id, is_available=True)
    reviews = package.reviews.all().order_by('-created_at')
    
    currency = request.session.get('currency', 'BDT')
    
    package.converted_price = convert_currency(package.price, to_currency=currency)
    package.currency_symbol = get_currency_symbol(currency)
    
    custom_components = package.custom_components or {}
    if custom_components.get('flight_price'):
        flight_price = Decimal(str(custom_components['flight_price']))
        custom_components['converted_flight_price'] = convert_currency(flight_price, to_currency=currency)
    if custom_components.get('hotel_price_per_night'):
        hotel_price = Decimal(str(custom_components['hotel_price_per_night']))
        custom_components['converted_hotel_price_per_night'] = convert_currency(hotel_price, to_currency=currency)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.package = package
            review.user_name = request.user
            review.save()
            return redirect('package_detail', package_id=package.id)
    else:
        form = ReviewForm()

    context = {
        'package': package,
        'reviews': reviews,
        'form': form,
        'selected_currency': currency,
        'custom_components': custom_components,
        'package_id': package_id,
    }
    return render(request, 'packages/package_detail.html', context)


@login_required
def buy_package(request, package_id):
    package = get_object_or_404(Package, id=package_id, is_available=True)
    
    if request.method == 'POST':
        if package.price > request.user.expense_threshold:
            Notification.objects.create(
                user=request.user,
                notification_type='expense_alert',
                message=f"Your booking for '{package.package_name}' exceeds your expense threshold of {request.user.expense_threshold} BDT."
            )
        
        # Create a Payment record with pending status
        payment = Payment.objects.create(
            package=package,
            user=request.user,
            amount=package.price,
            status='pending',
        )
        # Redirect to the custom payment gateway page
        return redirect('payment_gateway', payment_id=payment.id, package_id=package.id)

    return render(request, 'packages/buy_package.html', {'package': package})


@login_required
def payment_gateway(request, payment_id, package_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user, status='pending')
    package = get_object_or_404(Package, id=package_id, is_available=True)
    
    if request.method == 'POST':
        card_number = request.POST.get('card_number').strip()  
        cardholder_name = request.POST.get('cardholder_name')
        expiry_date = request.POST.get('expiry_date')
        cvv = request.POST.get('cvv')
        payment_method = request.POST.get('payment_method', 'Credit Card')

        if not (card_number and cardholder_name and expiry_date and cvv):
            return render(request, 'packages/payment_gateway.html', {
                'payment': payment,
                'error': 'All payment fields are required.',
            })

        if len(cvv) != 3:
            return render(request, 'packages/payment_gateway.html', {
                'payment': payment,
                'error': 'Invalid CVV. Please enter a 3-digit CVV.',
            })

        cleaned_card_number = ''.join(filter(str.isdigit, card_number))
        if len(cleaned_card_number) < 4:
            return render(request, 'packages/payment_gateway.html', {
                'payment': payment,
                'error': 'Invalid card number. Please enter a valid card number.',
            })

        masked_card_number = f"**** **** **** {cleaned_card_number[-4:]}"

        payment.card_number = masked_card_number
        payment.cardholder_name = cardholder_name
        payment.expiry_date = expiry_date
        payment.payment_method = payment_method
        payment.status = 'succeeded'
        payment.save()

        Notification.objects.create(
            user=request.user,
            notification_type='package_confirmation',
            message=f"Your booking for '{package.package_name}' has been confirmed!",
            package=package
        )

        return redirect('payment_success', payment_id=payment.id)

    return render(request, 'packages/payment_gateway.html', {'payment': payment})


@login_required
def payment_success(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    return render(request, 'packages/payment_success.html', {
        'package': payment.package,
        'payment': payment,
    })

@login_required
def payment_cancel(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    if payment.status == 'pending':
        payment.status = 'cancelled'
        payment.save()
    return render(request, 'packages/payment_cancel.html', {'package': payment.package})


@login_required
def create_custom_package(request):
    FLIGHTS = {
        ('DAC', 'LHR'): ('Emirates EK123', 50000),
        ('DAC', 'NYC'): ('Qatar Airways QR456', 60000),
        ('LHR', 'NYC'): ('British Airways BA789', 40000),
    }

    HOTELS = {
        'London': ('The Ritz London', 20000),
        'New York': ('The Plaza NYC', 25000),
    }

    if request.method == 'POST':
        if 'get_flight' in request.POST:
            source = request.POST.get('source')
            destination = request.POST.get('destination')
            flight_key = (source, destination)
            if flight_key in FLIGHTS:
                flight_name, flight_price = FLIGHTS[flight_key]
                return JsonResponse({'flight_name': flight_name, 'flight_price': flight_price})
            return JsonResponse({'error': 'No flight available for this route.'}, status=400)

        elif 'get_hotel' in request.POST:
            destination = request.POST.get('hotel_destination')
            if destination in HOTELS:
                hotel_name, hotel_price = HOTELS[destination]
                return JsonResponse({'hotel_name': hotel_name, 'hotel_price': hotel_price})
            return JsonResponse({'error': 'No hotel available for this destination.'}, status=400)

        elif 'buy_package' in request.POST:
            source = request.POST.get('source')
            destination = request.POST.get('destination')
            hotel_destination = request.POST.get('hotel_destination')
            check_in_date = request.POST.get('check_in_date')
            check_out_date = request.POST.get('check_out_date')
            num_guests = int(request.POST.get('num_guests', 1))
            airport_pickup = request.POST.get('airport_pickup') == 'on'  # Checkbox for airport pickup

            if not all([source, destination, hotel_destination, check_in_date, check_out_date]):
                messages.error(request, 'All fields are required.')
                return redirect('create_custom_package')

            check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
            if check_out <= check_in:
                messages.error(request, 'Check-out date must be after check-in date.')
                return redirect('create_custom_package')

            stay_days = (check_out - check_in).days

            flight_key = (source, destination)
            flight_name, flight_price = FLIGHTS.get(flight_key, ('Unknown Flight', 0))

            hotel_name, hotel_price_per_night = HOTELS.get(hotel_destination, ('Unknown Hotel', 0))
            hotel_total_price = hotel_price_per_night * stay_days

            total_price = flight_price + hotel_total_price + (num_guests * 5000)  # 5000 BDT per guest

            airport_pickup_fee = 5000 if airport_pickup else 0
            total_price += airport_pickup_fee

            package = Package.objects.create(
                package_name=f"Custom Package: {source} to {destination}",
                description=f"Flight: {flight_name}, Hotel: {hotel_name} in {hotel_destination}",
                price=total_price,
                duration=stay_days,
                created_by=request.user,
                custom_components={
                    'source': source,
                    'destination': destination,
                    'flight_name': flight_name,
                    'flight_price': flight_price,
                    'hotel_destination': hotel_destination,
                    'hotel_name': hotel_name,
                    'hotel_price_per_night': hotel_price_per_night,
                    'stay_days': stay_days,
                    'num_guests': num_guests,
                    'airport_pickup': airport_pickup,
                    'airport_pickup_fee': airport_pickup_fee,
                },
                start_date=check_in,
                end_date=check_out,
                is_available=False  # One-time use package
            )

            payment = Payment.objects.create(
                package=package,
                user=request.user,
                amount=package.price,
                status='pending',
            )

            return redirect('payment_gateway', payment_id=payment.id)

    return render(request, 'packages/custom_package.html', {
        'flight_sources': sorted(set(source for source, _ in FLIGHTS.keys())),
        'flight_destinations': sorted(set(dest for _, dest in FLIGHTS.keys())),
        'hotel_destinations': sorted(HOTELS.keys()),
    })