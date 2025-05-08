from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from ..models import Hotels, HotelRoom, Payment, Package
import json


@login_required
def hotel_booking(request):
    # Get all hotels and their available rooms
    hotels = Hotels.objects.prefetch_related('rooms').all()
    # Filter hotels to only show those with at least one available room
    hotels_with_available_rooms = [
        hotel for hotel in hotels if any(room.available_count > 0 for room in hotel.rooms.all())
    ]

    # Prepare hotel capacities as a dictionary for JSON serialization
    hotel_capacities = {}
    for hotel in hotels_with_available_rooms:
        capacities = [
            {'capacity': room.capacity, 'available': room.available_count}
            for room in hotel.rooms.all() if room.available_count > 0
        ]
        hotel_capacities[str(hotel.id)] = capacities

    # Convert to JSON
    hotel_capacities_json = json.dumps(hotel_capacities)

    if request.method == 'POST':
        hotel_id = request.POST.get('hotel_id')
        capacity = request.POST.get('capacity')
        check_in_date = request.POST.get('check_in_date')
        check_out_date = request.POST.get('check_out_date')
        num_guests = int(request.POST.get('num_guests', 1))

        # Validate required fields
        if not all([hotel_id, capacity, check_in_date, check_out_date]):
            messages.error(request, 'All fields are required.')
            return render(request, 'packages/hotel_booking.html', {
                'hotels': hotels_with_available_rooms,
                'hotel_capacities_json': hotel_capacities_json
            })

        # Validate dates
        check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
        if check_out <= check_in:
            messages.error(request, 'Check-out date must be after check-in date.')
            return render(request, 'packages/hotel_booking.html', {
                'hotels': hotels_with_available_rooms,
                'hotel_capacities_json': hotel_capacities_json
            })

        # Validate number of guests against capacity
        capacity = int(capacity)
        if num_guests > capacity:
            messages.error(request, 'Number of guests exceeds the selected room capacity.')
            return render(request, 'packages/hotel_booking.html', {
                'hotels': hotels_with_available_rooms,
                'hotel_capacities_json': hotel_capacities_json
            })

        # Calculate stay duration
        stay_days = (check_out - check_in).days

        # Get the selected hotel and room
        hotel = get_object_or_404(Hotels, id=hotel_id)
        hotel_room = get_object_or_404(HotelRoom, hotel=hotel, capacity=capacity)

        # Check if the room type is still available
        if hotel_room.available_count <= 0:
            messages.error(request, 'The selected room type is no longer available.')
            return render(request, 'packages/hotel_booking.html', {
                'hotels': hotels_with_available_rooms,
                'hotel_capacities_json': hotel_capacities_json
            })

        # Calculate total price
        total_price = hotel.price_per_night * stay_days + (num_guests * 5000)  # 5000 BDT per guest

        # Create a package for the hotel booking
        package = Package.objects.create(
            package_name=f"Hotel Booking: {hotel.name}",
            description=f"Hotel: {hotel.name} in {hotel.location}, {stay_days} nights, Room for {capacity} people",
            price=total_price,
            duration=stay_days,
            created_by=request.user,
            custom_components={
                'hotel_name': hotel.name,
                'location': hotel.location,
                'price_per_night': float(hotel.price_per_night),
                'stay_days': stay_days,
                'num_guests': num_guests,
                'capacity': capacity,
            },
            start_date=check_in,
            end_date=check_out,
            is_available=False  # One-time use package
        )

        # Create a Payment record with pending status
        payment = Payment.objects.create(
            package=package,
            user=request.user,
            amount=package.price,
            status='pending',
        )

        # Store the hotel_room ID in the session to update availability later
        request.session['hotel_room_id'] = hotel_room.id

        # Redirect to the payment gateway
        return redirect('payment_gateway', payment_id=payment.id)

    return render(request, 'packages/hotel_booking.html', {
        'hotels': hotels_with_available_rooms,
        'hotel_capacities_json': hotel_capacities_json
    })