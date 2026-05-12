from django.contrib import admin
from .models import Location, StaffAccount

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(StaffAccount)
class StaffAccountAdmin(admin.ModelAdmin):
    list_display = ('staffID', 'user', 'assigned_location', 'status')
    readonly_fields = ('staffID',)
