from django.contrib import admin
from .models import (Package, 
                     Booking, 
                     Payment, 
                     Hotels, 
                     HotelRoom,
                     Flights,
                     Review,
                     Voucher)

# Register your models here.
admin.site.register(Payment)
admin.site.register(Hotels)
admin.site.register(HotelRoom)
admin.site.register(Flights)
admin.site.register(Review)


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('package_name', 'price', 'is_available', 'start_date', 'end_date', 'created_by')
    list_filter = ('is_available', 'start_date')
    search_fields = ('package_name', 'description')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'package', 'booking_date', 'status')
    list_filter = ('status',)
    search_fields = ('user__username', 'package__package_name')


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('code', 'voucher_type', 'user', 'discount_amount', 'discount_percentage', 'is_active', 'created_at', 'expires_at')
    list_filter = ('voucher_type', 'is_active')
    search_fields = ('code', 'user__username')
    readonly_fields = ('code', 'created_at')