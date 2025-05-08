from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from django.http import JsonResponse  # Add this import for AJAX response
from ..models import Flights, Payment, Package

@login_required
def flight_booking(request):
    # Get unique sources and destinations for dropdowns
    sources = Flights.objects.filter(is_available=True).values_list('source', flat=True).distinct()
    destinations = Flights.objects.filter(is_available=True).values_list('destination', flat=True).distinct()

    # Initialize context with sources and destinations
    context = {
        'sources': sources,
        'destinations': destinations,
        'flights': [],
    }

    if request.method == 'POST':
        source = request.POST.get('source')
        destination = request.POST.get('destination')
        trip_type = request.POST.get('trip_type')  # "one-way" or "round-trip"
        departure_date = request.POST.get('departure_date')
        return_date = request.POST.get('return_date')
        num_passengers = int(request.POST.get('num_passengers', 1))

        # Validate required fields
        if not all([source, destination, trip_type, departure_date, num_passengers]):
            messages.error(request, 'All fields are required except return date for one-way trips.')
            return render(request, 'packages/flight_booking.html', context)

        # Validate source != destination
        if source == destination:
            messages.error(request, 'Source and destination cannot be the same.')
            return render(request, 'packages/flight_booking.html', context)

        # Validate dates
        departure = datetime.strptime(departure_date, '%Y-%m-%d').date()
        return_date = datetime.strptime(return_date, '%Y-%m-%d').date() if return_date else None
        if trip_type == 'round-trip' and not return_date:
            messages.error(request, 'Return date is required for round-trip bookings.')
            return render(request, 'packages/flight_booking.html', context)
        if return_date and return_date <= departure:
            messages.error(request, 'Return date must be after departure date.')
            return render(request, 'packages/flight_booking.html', context)

        # Calculate duration
        duration = 1 if not return_date else (return_date - departure).days

        # Find available flights for the selected source and destination
        flights = Flights.objects.filter(
            source=source,
            destination=destination,
            is_available=True
        )

        if not flights.exists():
            messages.error(request, f'No available flights from {source} to {destination}.')
            return render(request, 'packages/flight_booking.html', context)

        # Use the first available flight
        flight = flights.first()

        # Calculate total price
        total_price = flight.price * num_passengers * (2 if trip_type == 'round-trip' else 1)

        # Create a package for the flight booking
        package = Package.objects.create(
            package_name=f"Flight Booking: {flight.source} to {flight.destination}",
            description=f"Flight from {flight.source} to {flight.destination}, {duration} day(s), {num_passengers} passenger(s), {trip_type}",
            price=total_price,
            duration=duration,
            created_by=request.user,
            custom_components={
                'source': flight.source,
                'destination': flight.destination,
                'price': float(flight.price),
                'num_passengers': num_passengers,
                'trip_type': trip_type,
            },
            start_date=departure,
            end_date=return_date,
            is_available=False  # One-time use package
        )

        # Create a Payment record with pending status
        payment = Payment.objects.create(
            package=package,
            user=request.user,
            amount=package.price,
            status='pending',
        )

        # Redirect to the payment gateway
        return redirect('payment_gateway', payment_id=payment.id)

    return render(request, 'packages/flight_booking.html', context)

@login_required
def get_flight_price(request):
    if request.method == 'GET':
        source = request.GET.get('source')
        destination = request.GET.get('destination')

        if source and destination:
            # Fetch the flight price for the selected source and destination
            flight = Flights.objects.filter(
                source=source,
                destination=destination,
                is_available=True
            ).first()

            if flight:
                return JsonResponse({'price': float(flight.price), 'available': True})
            else:
                return JsonResponse({'price': 0, 'available': False, 'error': f'No available flights from {source} to {destination}.'})
        else:
            return JsonResponse({'price': 0, 'available': False, 'error': 'Source and destination are required.'})

    return JsonResponse({'error': 'Invalid request method.'}, status=400)