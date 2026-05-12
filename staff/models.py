from django.db import models
from django.contrib.auth.models import User

class Location(models.Model):
    name = models.CharField(max_length=255)
    short_code = models.CharField(max_length=5, default='')
    
    def __str__(self):
        return f"{self.name} ({self.short_code})"

class Vehicle(models.Model):
    vehicle_number = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.vehicle_number

class Driver(models.Model):
    user_name = models.CharField(max_length=255)
    license_number = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user_name} ({self.license_number})"

class Route(models.Model):
    from_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='starting_routes')
    to_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='ending_routes')
    route_path = models.JSONField(help_text="List of intermediate location names or IDs")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='assigned_routes')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='assigned_routes')

    def __str__(self):
        return f"Route from {self.from_location} to {self.to_location} via {len(self.route_path)} stops"

class StaffAccount(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='staff_account')
    staffID = models.CharField(max_length=20, unique=True, editable=False)
    assigned_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_accounts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.staffID:
            # Get the last staff account to determine the next ID
            last_staff = StaffAccount.objects.all().order_by('id').last()
            if not last_staff:
                new_id = 1
            else:
                new_id = last_staff.id + 1
            self.staffID = f'staff-{new_id}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} ({self.staffID})"

class Payment(models.Model):
    STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('To Pay', 'To Pay'),
    ]
    MODE_CHOICES = [
        ("None", "None"),
        ('Cash', 'Cash'),
        ('Online', 'Online'),
    ]

    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Paid')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='None')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} ({self.mode}) - {self.status}"

class Courier(models.Model):
    DELIVERY_TYPE_CHOICES = [
        ('GoodDown Delivery', 'GoodDown Delivery'),
        ('Door Delivery', 'Door Delivery'),
    ]
    STATUS_CHOICES = [
        ('inplace', 'In Place'),
        ('shipping', 'Shipping'),
        ('delivered', 'Delivered'),
    ]

    created_by = models.ForeignKey(StaffAccount, on_delete=models.CASCADE, related_name='created_couriers')
    from_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='outgoing_couriers')
    to_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='incoming_couriers')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='couriers')
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name='couriers')
    
    sender_name = models.CharField(max_length=255)
    receiver_name = models.CharField(max_length=255)
    from_address = models.TextField()
    to_address = models.TextField()
    sender_phone_num = models.CharField(max_length=15)
    receiver_phone_num = models.CharField(max_length=15)
    
    parcel_information = models.JSONField()  # List of lists e.g., [["nature1", 5], ["nature2", 6]]
    weight = models.PositiveIntegerField()
    
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='courier')
    invoice_number = models.CharField(max_length=20)
    lr_number = models.CharField(max_length=50, unique=True, editable=False, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inplace')
    delivered_to_customer = models.BooleanField(default=False)
    
    freight = models.PositiveIntegerField(default=0)
    loading_unloading = models.PositiveIntegerField(default=0)
    door_pickup = models.PositiveIntegerField(default=0)
    other_transport_crossing = models.PositiveIntegerField(default=0)
    mamool = models.PositiveIntegerField(default=0)
    statistical_charges = models.PositiveIntegerField(default=0)
    door_delivery = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_TYPE_CHOICES)

    @property
    def total(self):
        return (
            self.freight +
            self.loading_unloading +
            self.door_pickup +
            self.other_transport_crossing +
            self.mamool +
            self.statistical_charges +
            self.door_delivery
        )

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and not self.lr_number:
            short_code = self.from_location.short_code if self.from_location else "UNK"
            self.lr_number = f"LR-{short_code}-{self.id}"
            # Save again to store the lr_number
            super().save(update_fields=['lr_number'])

    def __str__(self):
        return f"Courier {self.lr_number or self.invoice_number} - {self.sender_name} to {self.receiver_name}"

class GDM(models.Model):
    gdm_number = models.CharField(max_length=50, unique=True, editable=False, null=True, blank=True)
    created_by = models.ForeignKey(StaffAccount, on_delete=models.CASCADE, related_name='created_gdms', null=True, blank=True)
    vehicle_number = models.CharField(max_length=20)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='gdms')
    couriers = models.ManyToManyField(Courier, related_name='gdms')
    dispatch_date = models.DateTimeField(auto_now_add=True)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='gdms')

    @property
    def status(self):
        couriers = self.couriers.all()
        if not couriers.exists():
            return "unshipped"
        
        statuses = set(couriers.values_list('status', flat=True))
        
        if 'inplace' in statuses:
            return "inplace"
        if 'shipping' in statuses:
            return "shipping"
        if all(s == 'delivered' for s in statuses):
            return "sent"
            
        return "unshipped"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and not self.gdm_number:
            location = self.created_by.assigned_location
            short_code = location.short_code if location else "UNK"
            self.gdm_number = f"GDM-{short_code}-{self.id}"
            super().save(update_fields=['gdm_number'])

    @property
    def total_weights(self):
        return sum(c.weight for c in self.couriers.all())

    @property
    def total_couriers_count(self):
        return self.couriers.count()

    @property
    def total_price(self):
        return sum(c.total for c in self.couriers.all())

    @property
    def driver_name(self):
        return self.driver.user_name

    @property
    def all_locations(self):
        path = [self.route.from_location.name]
        path.extend(self.route.route_path)
        path.append(self.route.to_location.name)
        return path

    @property
    def driver_phone_num(self):
        return self.driver.phone_number

    def __str__(self):
        return f"GDM {self.id} - {self.vehicle_number} on {self.dispatch_date.date()}"
