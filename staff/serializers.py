from rest_framework import serializers
from .models import Courier, Payment, Location, Driver, Route, Vehicle, GDM, Reason, Expense, Account



class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ['id', 'user_name', 'license_number', 'phone_number']

class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'from_location', 'to_location', 'route_path', 'driver', 'vehicle']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['from_location'] = LocationSerializer(instance.from_location).data
        rep['to_location'] = LocationSerializer(instance.to_location).data
        rep['driver'] = DriverSerializer(instance.driver).data
        rep['vehicle'] = VehicleSerializer(instance.vehicle).data
        return rep

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'vehicle_number']

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name']

class CourierSerializer(serializers.ModelSerializer):
    payment_status = serializers.ChoiceField(choices=Payment.STATUS_CHOICES, write_only=True)
    payment_mode = serializers.ChoiceField(choices=Payment.MODE_CHOICES, write_only=True)
    
    class Meta:
        model = Courier
        fields = [
            'id', 'from_location', 'to_location', 'vehicle', 'sender_name', 'receiver_name', 'from_address',
            'to_address', 'sender_phone_num', 'receiver_phone_num', 
            'parcel_information', 'weight', 'invoice_number', 'freight', 
            'loading_unloading', 'door_pickup', 'other_transport_crossing', 
            'mamool', 'statistical_charges', 'door_delivery', 'delivery_type',
            'payment_status', 'payment_mode', 'total', 'lr_number', 'status', 'route', 'delivered_to_customer',
            'getting_person_name', 'getting_person_ph'
        ]
        read_only_fields = ['id', 'total', 'from_location']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['from_location'] = LocationSerializer(instance.from_location).data
        rep['to_location'] = LocationSerializer(instance.to_location).data
        if instance.vehicle:
            rep['vehicle'] = VehicleSerializer(instance.vehicle).data
        if instance.route:
            rep['route'] = RouteSerializer(instance.route).data
        if hasattr(instance, 'payment') and instance.payment:
            rep['payment_status'] = instance.payment.status
            rep['payment_mode'] = instance.payment.mode
        return rep

    def create(self, validated_data):
        payment_status = validated_data.pop('payment_status')
        payment_mode = validated_data.pop('payment_mode')
        
        # Calculate total
        charges = [
            validated_data.get('freight', 0),
            validated_data.get('loading_unloading', 0),
            validated_data.get('door_pickup', 0),
            validated_data.get('other_transport_crossing', 0),
            validated_data.get('mamool', 0),
            validated_data.get('statistical_charges', 0),
            validated_data.get('door_delivery', 0),
        ]
        total_amount = sum(charges)
        
        # Create Payment
        payment = Payment.objects.create(
            amount=total_amount,
            status=payment_status,
            mode=payment_mode
        )
        
        # Create Courier
        courier = Courier.objects.create(payment=payment, **validated_data)
        return courier

class GDMSerializer(serializers.ModelSerializer):
    total_weights = serializers.ReadOnlyField()
    total_couriers_count = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()
    driver_name = serializers.ReadOnlyField()
    driver_phone_num = serializers.ReadOnlyField()

    class Meta:
        model = GDM
        fields = [
            'id', 'gdm_number', 'vehicle_number', 'driver', 'route', 'couriers', 
            'dispatch_date', 'status', 'total_weights', 'all_locations',
            'total_couriers_count', 'total_price', 'driver_name', 'driver_phone_num'
        ]
        read_only_fields = ['id', 'gdm_number', 'dispatch_date', 'status']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['driver'] = DriverSerializer(instance.driver).data
        rep['route'] = RouteSerializer(instance.route).data
        return rep

class ReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reason
        fields = ['id', 'name']

class ExpenseSerializer(serializers.ModelSerializer):
    reason_name = serializers.ReadOnlyField(source='reason.name')

    class Meta:
        model = Expense
        fields = ['id', 'reason', 'reason_name', 'staff', 'text', 'amount', 'created_at']
        read_only_fields = ['staff', 'created_at']

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['revenue', 'spent', 'balance', 'updated_date']
