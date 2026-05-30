from rest_framework import serializers
from django.contrib.auth.models import User
from staff.models import StaffAccount, Location, Expense, GDM, Driver, Vehicle, Courier

class StaffUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    assigned_location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all(), required=False, allow_null=True)
    status = serializers.ChoiceField(choices=StaffAccount.STATUS_CHOICES, default='active')

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'assigned_location', 'status']

    def create(self, validated_data):
        assigned_location = validated_data.pop('assigned_location', None)
        status = validated_data.pop('status', 'active')
        password = validated_data.pop('password')
        
        # Create the user
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create the associated StaffAccount
        StaffAccount.objects.create(
            user=user,
            assigned_location=assigned_location,
            status=status
        )
        return user

class AdminExpenseSerializer(serializers.ModelSerializer):
    reason_name = serializers.ReadOnlyField(source='reason.name')
    staff_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = ['id', 'reason', 'reason_name', 'staff', 'staff_name', 'branch_name', 'text', 'amount', 'created_at']

    def get_staff_name(self, obj):
        return obj.staff.user.get_full_name() or obj.staff.user.username

    def get_branch_name(self, obj):
        if obj.staff.assigned_location:
            return obj.staff.assigned_location.name
        return None

class DispatchMemoSerializer(serializers.ModelSerializer):
    route = serializers.SerializerMethodField()
    driver = serializers.CharField(source='driver.user_name')
    lrs = serializers.SerializerMethodField()
    freight = serializers.SerializerMethodField()

    class Meta:
        model = GDM
        fields = ['gdm_number', 'route', 'vehicle_number', 'driver', 'lrs', 'freight']

    def get_route(self, obj):
        return obj.all_locations

    def get_lrs(self, obj):
        return obj.couriers.count()

    def get_freight(self, obj):
        return sum(c.freight for c in obj.couriers.all())

class StaffListSerializer(serializers.ModelSerializer):
    staff_id = serializers.CharField(source='staffID')
    name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email')
    assigned_location = serializers.SerializerMethodField()

    class Meta:
        model = StaffAccount
        fields = ['id', 'staff_id', 'name', 'email', 'assigned_location', 'status']

    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_assigned_location(self, obj):
        return obj.assigned_location.name if obj.assigned_location else None

class DriverListSerializer(serializers.ModelSerializer):
    driver_id = serializers.IntegerField(source='id')
    name = serializers.CharField(source='user_name')
    phone_num = serializers.CharField(source='phone_number')
    status = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = ['driver_id', 'name', 'phone_num', 'status']

    def get_status(self, obj):
        return 'active'

class DriverCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(write_only=True)

    class Meta:
        model = Driver
        fields = ['name', 'phone_number']

    def create(self, validated_data):
        name = validated_data.get('name')
        phone_number = validated_data.get('phone_number')

        import uuid
        base_username = name.lower().replace(" ", "_")
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        # 1. Create User account first with password 'pass'
        user = User.objects.create_user(
            username=username,
            password='pass',
            first_name=name
        )

        # 2. Generate unique license number for Driver
        license_number = f"LIC-{uuid.uuid4().hex[:8].upper()}"
        while Driver.objects.filter(license_number=license_number).exists():
            license_number = f"LIC-{uuid.uuid4().hex[:8].upper()}"

        # 3. Create the Driver record in the database
        driver = Driver.objects.create(
            user_name=name,
            license_number=license_number,
            phone_number=phone_number
        )

        return driver

    def to_representation(self, instance):
        return DriverListSerializer(instance).data

class StaffCreateSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    assigned_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = StaffAccount
        fields = ['full_name', 'email', 'password', 'assigned_location']

    def create(self, validated_data):
        full_name = validated_data.get('full_name')
        email = validated_data.get('email')
        password = validated_data.get('password')
        assigned_location = validated_data.get('assigned_location')

        base_username = full_name.lower().replace(" ", "_")
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        # 1. Create Django User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=full_name
        )

        # 2. Create associated StaffAccount record
        staff = StaffAccount.objects.create(
            user=user,
            assigned_location=assigned_location,
            status='active'
        )

        return staff

    def to_representation(self, instance):
        return StaffListSerializer(instance).data

class VehicleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'vehicle_number']

class VehicleCreateSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(write_only=True)
    vehicle_name = serializers.CharField(write_only=True, source='vehicle_number')

    class Meta:
        model = Vehicle
        fields = ['driver_name', 'vehicle_name']

    def create(self, validated_data):
        driver_name = validated_data.get('driver_name')
        vehicle_number = validated_data.get('vehicle_number')

        # 1. Create or get the Driver
        import uuid
        driver, created = Driver.objects.get_or_create(
            user_name=driver_name,
            defaults={
                'license_number': f"LIC-{uuid.uuid4().hex[:8].upper()}",
                'phone_number': ''
            }
        )

        # 2. Create the Vehicle record
        vehicle = Vehicle.objects.create(
            vehicle_number=vehicle_number
        )

        return vehicle

    def to_representation(self, instance):
        return VehicleListSerializer(instance).data

class CourierGDMDetailsSerializer(serializers.ModelSerializer):
    lr_num = serializers.CharField(source='lr_number')
    customer_name = serializers.CharField(source='receiver_name')
    route = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    freight = serializers.IntegerField()

    class Meta:
        model = Courier
        fields = ['lr_num', 'customer_name', 'route', 'status', 'freight']

    def get_route(self, obj):
        if obj.route:
            return f"{obj.route.from_location.name} -> {obj.route.to_location.name}"
        return f"{obj.from_location.name} -> {obj.to_location.name}"

    def get_status(self, obj):
        if obj.payment:
            return 'paid' if obj.payment.status == 'Paid' else 'not paid'
        return 'not paid'

class GDMDetailsSerializer(serializers.ModelSerializer):
    vehicle_number = serializers.CharField()
    driver_name = serializers.CharField(source='driver.user_name')
    couriers = CourierGDMDetailsSerializer(many=True)
    total_freight = serializers.SerializerMethodField()

    class Meta:
        model = GDM
        fields = ['gdm_number', 'vehicle_number', 'driver_name', 'couriers', 'total_freight']

    def get_total_freight(self, obj):
        return sum(c.freight for c in obj.couriers.all())






