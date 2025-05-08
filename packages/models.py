from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

from decimal import Decimal



# Create your models here.
# Map this with the package model that admin creates
class Package(models.Model):
    package_name = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField(null=True, blank=True)
    image = models.ImageField(upload_to='package_images/', null=True, blank=True)
    custom_components = models.JSONField(null=True, blank=True)
    is_trending = models.BooleanField(default=False)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    included_services = models.TextField(blank=True)
    travel_tips = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    policy = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.package_name
    

class CustomPackage(models.Model):
    package = models.OneToOneField(Package, on_delete=models.CASCADE, related_name='custom_details')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    flight_details = models.JSONField(blank=True, null=True)  # Store flight data (e.g., Amadeus response)
    hotel_details = models.JSONField(blank=True, null=True)  # Store hotel data (e.g., Hotelbeds response)

    def __str__(self):
        return f"Custom: {self.package.name} by {self.user.username}"


class Review(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='reviews')
    user_name = models.CharField(max_length=100) # Kept separate from user auths for l3, will treate it separately from module 1's
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_name} - {self.package}"
    

class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')],
        default='pending'
    )

    def __str__(self):
        return f"{self.user.username} - {self.package.package_name}"
    

class Payment(models.Model):
    package = models.ForeignKey('Package', on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')  # e.g., 'pending', 'succeeded', 'failed', 'refunded'
    created_at = models.DateTimeField(auto_now_add=True)
    card_number = models.CharField(max_length=22, blank=True)  # Last 4 digits for display (e.g., "**** **** **** 1234")
    cardholder_name = models.CharField(max_length=100, blank=True)
    expiry_date = models.CharField(max_length=10, blank=True)  # Format: MM/YY
    payment_method = models.CharField(max_length=50, blank=True)  # e.g., "Credit Card", "Debit Card"

    def __str__(self):
        return f"Payment for {self.package.package_name} by {self.user.username}"


class Voucher(models.Model):
    VOUCHER_TYPE_CHOICES = [
        ('REGISTRATION', 'Registration'),
        ('PURCHASE', 'Purchase-Based'),
        ('GIFT', 'Gift'),
    ]
    code = models.CharField(max_length=20, unique=True, blank=True)
    voucher_type = models.CharField(max_length=20, choices=VOUCHER_TYPE_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vouchers')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], null=True, blank=True)
    discount_percentage = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.voucher_type} Voucher ({self.code}) for {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.code and self.voucher_type == 'GIFT':
            import uuid
            self.code = str(uuid.uuid4())[:12].upper()  # Generate unique code for gift vouchers
        super().save(*args, **kwargs)

    def apply_discount(self, amount):
        """Apply the voucher discount to an amount (in BDT)."""
        if not self.is_active or self.used_at:
            return amount
        if self.discount_amount:
            return max(Decimal('0'), amount - self.discount_amount)
        if self.discount_percentage:
            discount = (self.discount_percentage / Decimal('100')) * amount
            return max(Decimal('0'), amount - discount)
        return amount
    

# STANDALONE MODELS
class Hotels(models.Model):
    name = models.CharField(max_length=100)  # e.g., "The Ritz London"
    location = models.CharField(max_length=100)  # e.g., "London"
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)  # e.g., 20000.00 BDT
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} in {self.location}"
    

class HotelRoom(models.Model):
    hotel = models.ForeignKey(Hotels, on_delete=models.CASCADE, related_name='rooms')
    capacity = models.IntegerField()  # Number of people the room can accommodate (e.g., 2, 4, 5)
    available_count = models.IntegerField(default=3)  # Up to 3 rooms of this type available

    class Meta:
        unique_together = ('hotel', 'capacity')  # Ensure each hotel has only one room type per capacity

    def __str__(self):
        return f"Room for {self.capacity} people at {self.hotel.name} ({self.available_count} available)"


class Flights(models.Model):
    source = models.CharField(max_length=100)  # e.g., "Cox's Bazar"
    destination = models.CharField(max_length=100)  # e.g., "London"
    price = models.DecimalField(max_digits=10, decimal_places=2)  # e.g., 50000.00 BDT
    is_available = models.BooleanField(default=True)  # Whether the flight is available
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source} to {self.destination} (BDT {self.price})"