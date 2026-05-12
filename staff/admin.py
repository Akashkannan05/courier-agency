from django.contrib import admin
from .models import Location, Vehicle, Driver, Route, StaffAccount, Payment, Courier, GDM

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_code')
    search_fields = ('name', 'short_code')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_number',)
    search_fields = ('vehicle_number',)

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'license_number', 'phone_number')
    search_fields = ('user_name', 'license_number', 'phone_number')

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('from_location', 'to_location', 'driver', 'vehicle')
    list_filter = ('from_location', 'to_location')

@admin.register(StaffAccount)
class StaffAccountAdmin(admin.ModelAdmin):
    list_display = ('staffID', 'user', 'assigned_location', 'status')
    readonly_fields = ('staffID',)
    list_filter = ('status', 'assigned_location')
    search_fields = ('staffID', 'user__username')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('amount', 'status', 'mode', 'created_at')
    list_filter = ('status', 'mode')

@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    list_display = ('lr_number', 'invoice_number', 'sender_name', 'receiver_name', 'status', 'created_at')
    list_filter = ('status', 'delivery_type', 'from_location', 'to_location')
    search_fields = ('lr_number', 'invoice_number', 'sender_name', 'receiver_name')
    readonly_fields = ('lr_number',)

@admin.register(GDM)
class GDMAdmin(admin.ModelAdmin):
    list_display = ('gdm_number', 'vehicle_number', 'driver', 'status', 'dispatch_date')
    list_filter = ('dispatch_date',)
    search_fields = ('gdm_number', 'vehicle_number', 'driver__user_name')
    readonly_fields = ('gdm_number',)
