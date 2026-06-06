from django.db.models import Q
from django.contrib.auth import authenticate
from rest_framework import generics, permissions, status, response
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import HttpResponse
from django.utils import timezone
from .models import Courier, StaffAccount, Location, Route, Driver, Vehicle, GDM, Reason, Account, Expense
from .serializers import (
    CourierSerializer, LocationSerializer, RouteSerializer, 
    DriverSerializer, VehicleSerializer, GDMSerializer, ReasonSerializer,
    ExpenseSerializer, AccountSerializer
)
from .utils import generate_courier_pdf, generate_gdm_pdf, send_sms

class GDMCreateView(generics.CreateAPIView):
    serializer_class = GDMSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        courier_ids = request.data.get('couriers', [])
        if not courier_ids:
            return response.Response({"error": "couriers list is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        couriers = Courier.objects.filter(id__in=courier_ids)
        if couriers.count() != len(courier_ids):
            return response.Response({"error": "Some couriers not found"}, status=status.HTTP_404_NOT_FOUND)
            
        # Check if all couriers have the same route and vehicle
        routes = set(couriers.values_list('route', flat=True))
        vehicles = set(couriers.values_list('vehicle', flat=True))
        
        if len(routes) > 1:
            return response.Response({"error": "All couriers must belong to the same route"}, status=status.HTTP_400_BAD_REQUEST)
        if len(vehicles) > 1:
            return response.Response({"error": "All couriers must belong to the same vehicle"}, status=status.HTTP_400_BAD_REQUEST)
            
        route_id = list(routes)[0]
        vehicle_id = list(vehicles)[0]
        
        if route_id is None:
            return response.Response({"error": "Couriers must have an assigned route"}, status=status.HTTP_400_BAD_REQUEST)
            
        route = Route.objects.get(id=route_id)
        # vehicle_id might be None if courier.vehicle is not set, but usually it should be set if route is set.
        # But let's use the route's vehicle if available.
        vehicle = route.vehicle
        
        staff_account = StaffAccount.objects.filter(user=request.user).first()
        if not staff_account:
             return response.Response({"error": "Staff account not found"}, status=status.HTTP_404_NOT_FOUND)

        gdm = GDM.objects.create(
            created_by=staff_account,
            vehicle_number=vehicle.vehicle_number,
            driver=route.driver,
            route=route
        )
        gdm.couriers.set(couriers)
        gdm.save()
        
        serializer = self.get_serializer(gdm)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

class GDMListView(generics.ListAPIView):
    serializer_class = GDMSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        staff_account = StaffAccount.objects.filter(user=self.request.user).first()
        if not staff_account:
            return GDM.objects.none()
        return GDM.objects.filter(created_by=staff_account).order_by('-dispatch_date')

class GDMDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GDMSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        staff_account = StaffAccount.objects.filter(user=self.request.user).first()
        if not staff_account:
            return GDM.objects.none()
        return GDM.objects.filter(created_by=staff_account)

class StaffLoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        staff_id = request.data.get('staffID')
        password = request.data.get('password')
        
        if not staff_id or not password:
            return response.Response({"error": "staffID and password are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            staff_account = StaffAccount.objects.get(staffID=staff_id)
            user = authenticate(username=staff_account.user.username, password=password)
            
            if user:
                refresh = RefreshToken.for_user(user)
                return response.Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'staffID': staff_account.staffID,
                    'username': user.username
                }, status=status.HTTP_200_OK)
            else:
                return response.Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        except StaffAccount.DoesNotExist:
            return response.Response({"error": "Staff account not found"}, status=status.HTTP_404_NOT_FOUND)

class OtherLocationListView(generics.ListAPIView):
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        staff_account = StaffAccount.objects.filter(user=self.request.user).first()
        if not staff_account:
            return Location.objects.all()
        assigned_location = staff_account.assigned_location
        if assigned_location:
            return Location.objects.exclude(id=assigned_location.id)
        return Location.objects.all()

class CourierListView(generics.ListAPIView):
    serializer_class = CourierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        staff_account = StaffAccount.objects.get(user=self.request.user)
        if not staff_account:
            return Location.objects.all()
        assigned_location = staff_account.assigned_location
        if not assigned_location:
            return Courier.objects.none()
            
        status_filter = self.request.query_params.get('status', 'all').lower()
        
        queryset = Courier.objects.all()
        
        if status_filter == 'inplace':
            return queryset.filter(status='inplace', from_location=assigned_location)
        elif status_filter == 'shipping':
            return queryset.filter(status='shipping', from_location=assigned_location)
        elif status_filter == 'sent':
            return queryset.filter(status='delevered', from_location=assigned_location)
        elif status_filter == 'incoming':
            return queryset.filter(
                status='shipping',
                to_location=assigned_location
            )
        elif status_filter == 'recieved':
            return queryset.filter(status='delevered', to_location=assigned_location)
        else: # 'all' or any other value
            return queryset.filter(
                Q(from_location=assigned_location) | 
                (Q(to_location=assigned_location) & ~Q(status='inplace'))
            )

class DeleveredCourierListView(generics.ListAPIView):
    serializer_class = CourierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        staff_account = StaffAccount.objects.filter(user=self.request.user).first()
        if not staff_account or not staff_account.assigned_location:
            return Courier.objects.none()
            
        return Courier.objects.filter(
            status='delevered',
            to_location=staff_account.assigned_location,
            delivered_to_customer=True
        )

class PaidCourierListView(generics.ListAPIView):
    serializer_class = CourierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        staff_account = StaffAccount.objects.filter(user=self.request.user).first()
        if not staff_account or not staff_account.assigned_location:
            return Courier.objects.none()
            
        return Courier.objects.filter(
            status='delevered',
            to_location=staff_account.assigned_location,
            delivered_to_customer=False,
            payment__status='Paid'
        )

class ToPayCourierListView(generics.ListAPIView):
    serializer_class = CourierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        staff_account = StaffAccount.objects.filter(user=self.request.user).first()
        if not staff_account or not staff_account.assigned_location:
            return Courier.objects.none()
            
        return Courier.objects.filter(
            status='delevered',
            to_location=staff_account.assigned_location,
            delivered_to_customer=False,
            payment__status='To Pay'
        )

class CourierDetailView(generics.RetrieveUpdateAPIView):
    queryset = Courier.objects.all()
    serializer_class = CourierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        delivered_to_customer = request.data.get('delivered_to_customer')
        payment_status = request.data.get('payment_status')
        payment_mode = request.data.get('payment_mode')
        getting_person_name = request.data.get('getting_person_name')
        getting_person_ph = request.data.get('getting_person_ph')
        
        if getting_person_name:
            instance.getting_person_name = getting_person_name
        if getting_person_ph:
            instance.getting_person_ph = getting_person_ph

        if delivered_to_customer is not None:
            old_delivered = instance.delivered_to_customer
            instance.delivered_to_customer = delivered_to_customer
            instance.save()
            
            if not old_delivered and delivered_to_customer:
                # Send SMS Notification
                print(f"Sending 'delivered to customer' SMS for courier {instance.lr_number}...")
                sms_body = (
                    f"Dear Customer,\n"
                    f"Your parcel has been successfully delivered by Sa Salem Super Service.\n"
                    f"LR No: {instance.lr_number}\n"
                    f"From: {instance.from_address}\n"
                    f"To: {instance.to_address}\n"
                    f"Received By: {instance.getting_person_name}-{instance.getting_person_ph}\n"
                    f"Thank you for choosing Sa Salem Super Service. We appreciate your trust and look forward to serving you again.\n"
                    f"For any queries, contact us at +919788321354"
                )
                send_sms(instance.sender_phone_num, sms_body)
                send_sms(instance.receiver_phone_num, sms_body)
            
        if payment_status and hasattr(instance, 'payment') and instance.payment:
            old_status = instance.payment.status
            instance.payment.status = payment_status
            if payment_mode:
                instance.payment.mode = payment_mode
            instance.payment.save()
            
            if old_status != 'Paid' and payment_status == 'Paid':
                staff_account = StaffAccount.objects.filter(user=request.user).first()
                if staff_account:
                    account, _ = Account.objects.get_or_create(staff=staff_account)
                    account.ensure_today()
                    account.revenue += instance.total
                    account.save()
            
        return super().partial_update(request, *args, **kwargs)

class CourierCreateView(generics.CreateAPIView):
    serializer_class = CourierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save the courier
        staff_account = StaffAccount.objects.filter(user=self.request.user).first()
        if not staff_account:
            return response.Response({"error": "Staff account not found"}, status=status.HTTP_404_NOT_FOUND)
        
        courier = serializer.save(
            created_by=staff_account,
            from_location=staff_account.assigned_location
        )

        if courier.payment.status == 'Paid':
            account, _ = Account.objects.get_or_create(staff=staff_account)
            account.ensure_today()
            account.revenue += courier.total
            account.save()

        print(f"Sending 'booked' SMS for courier {courier.lr_number}...")
        sms_body = (
            f"Dear Customer,\n"
            f"Your parcel has been booked with Sa Salem Super Service.\n"
            f"LR No: {courier.lr_number}\n"
            f"From: {courier.from_address}\n"
            f"To: {courier.to_address}\n"
            f"Amount: Rs.{courier.total}\n"
            f"Payment Status: {courier.payment.status}\n"
            f"For support, contact us at +919788321354\n"
            f"Thank you for choosing Sa Salem Super Service."
        )

        send_sms(courier.sender_phone_num, sms_body)
        send_sms(courier.receiver_phone_num, sms_body)
        # Generate PDF
        no_of_packages = 0
        if courier.parcel_information and isinstance(courier.parcel_information, list):
            for item in courier.parcel_information:
                if isinstance(item, list) and len(item) > 1:
                    try:
                        no_of_packages += int(item[1])
                    except (ValueError, TypeError):
                        pass

        courier_data = {
            "invoice_number": courier.invoice_number,
            "date": courier.created_at.strftime("%d-%m-%Y") if courier.created_at else "",
            "from_location": courier.from_location.name if courier.from_location else "",
            "to_location": courier.to_location.name if courier.to_location else "",
            "sender_name": courier.sender_name,
            "sender_phone_num": courier.sender_phone_num,
            "from_address": courier.from_address,
            "receiver_name": courier.receiver_name,
            "receiver_phone_num": courier.receiver_phone_num,
            "to_address": courier.to_address,
            "no_of_packages": str(no_of_packages),
            "weight": str(courier.weight),
            "delivery_type": courier.delivery_type,
            "parcel_information": courier.parcel_information,
            "freight": courier.freight,
            "loading_unloading": courier.loading_unloading,
            "door_pickup": courier.door_pickup,
            "dd_charges": courier.door_delivery,
            "other_transport_crossing": courier.other_transport_crossing,
            "mamool": courier.mamool,
            "statistical_charges": courier.statistical_charges,
            "total": courier.total,
            "payment_status": courier.payment.status if courier.payment else "",
            "booked_by": (courier.created_by.user.get_full_name() or courier.created_by.user.username) if courier.created_by and courier.created_by.user else ""
        }

        pdf_buffer = generate_courier_pdf(courier_data)
        
        # Return PDF response
        response_obj = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf', status=status.HTTP_201_CREATED)
        response_obj['Access-Control-Expose-Headers'] = 'Content-Disposition'
        response_obj['Content-Disposition'] = f'attachment; filename="courier_{courier.invoice_number}.pdf"'
        return response_obj

class CourierAssignRouteView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CourierSerializer

    def patch(self, request, *args, **kwargs):
        courier_id = request.data.get('courier_id')
        route_id = request.data.get('route_id')
        
        if not courier_id or not route_id:
            return response.Response({"error": "courier_id and route_id are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            courier = Courier.objects.get(id=courier_id)
            route = Route.objects.get(id=route_id)
            
            courier.route = route
            courier.vehicle = route.vehicle
            # courier.status = 'shipping'
            courier.save()
            
            serializer = self.get_serializer(courier)
            return response.Response(serializer.data, status=status.HTTP_200_OK)
        except Courier.DoesNotExist:
            return response.Response({"error": "Courier not found"}, status=status.HTTP_404_NOT_FOUND)
        except Route.DoesNotExist:
            return response.Response({"error": "Route not found"}, status=status.HTTP_404_NOT_FOUND)

class CourierMarkShippingView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CourierSerializer

    def patch(self, request, pk=None, *args, **kwargs):
        staff_account = StaffAccount.objects.filter(user=request.user).first()
        if not staff_account:
            return response.Response({"error": "Staff account not found"}, status=status.HTTP_404_NOT_FOUND)
            
        courier_ids = request.data.get('courier_ids')

        if courier_ids and isinstance(courier_ids, list):
            # Bulk update
            updated_couriers = []
            couriers = Courier.objects.filter(id__in=courier_ids)
            
            # First check if all couriers have a route assigned
            for courier in couriers:
                if not courier.route:
                    return response.Response(
                        {"error": f"Courier {courier.lr_number or courier.id} does not have an assigned route"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            for courier in couriers:
                # Silently skip if not inplace or not from staff's location
                if courier.status == 'inplace' and courier.from_location == staff_account.assigned_location:
                    courier.status = 'shipping'
                    courier.save()
                    updated_couriers.append(courier)
            
            serializer = self.get_serializer(updated_couriers, many=True)
            return response.Response(serializer.data, status=status.HTTP_200_OK)
            
        else:
            # Single update (using pk from URL)
            if not pk:
                return response.Response({"error": "courier_ids list or URL pk is required"}, status=status.HTTP_400_BAD_REQUEST)
                
            try:
                courier = Courier.objects.get(pk=pk)
                if courier.status != 'inplace':
                    return response.Response({"error": "Courier is not in 'inplace' status"}, status=status.HTTP_400_BAD_REQUEST)
                    
                if courier.from_location != staff_account.assigned_location:
                    return response.Response({"error": "This courier is not at your assigned location"}, status=status.HTTP_403_FORBIDDEN)
                
                if not courier.route:
                    return response.Response({"error": "Courier does not have an assigned route"}, status=status.HTTP_400_BAD_REQUEST)

                courier.status = 'shipping'
                courier.save()
                
                serializer = self.get_serializer(courier)
                return response.Response(serializer.data, status=status.HTTP_200_OK)
            except Courier.DoesNotExist:
                return response.Response({"error": "Courier not found"}, status=status.HTTP_404_NOT_FOUND)

class CourierMarkDeleveredView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CourierSerializer

    def patch(self, request, pk=None, *args, **kwargs):
        staff_account = StaffAccount.objects.filter(user=request.user).first()
        if not staff_account:
            return response.Response({"error": "Staff account not found"}, status=status.HTTP_404_NOT_FOUND)
            
        courier_ids = request.data.get('courier_ids')

        if courier_ids and isinstance(courier_ids, list):
            # Bulk update
            updated_couriers = []
            couriers = Courier.objects.filter(id__in=courier_ids)
            for courier in couriers:
                # Silently skip if not shipping or not arriving at staff's location
                if courier.status == 'shipping' and courier.to_location == staff_account.assigned_location:
                    courier.status = 'delevered'
                    courier.save()
                    
                    # Send SMS Notification
                    print(f"Sending 'reached' SMS for courier {courier.lr_number}...")
                    sms_body = (
                        f"Dear Customer,\n"
                        f"Your parcel has reached the Sa Salem Super Service office successfully.\n"
                        f"LR No: {courier.lr_number}\n"
                        f"From: {courier.from_address}\n"
                        f"To: {courier.to_address}\n"
                        f"You may contact the destination office for delivery or pickup details.\n"
                        f"For support, contact us at +919788321354\n"
                        f"Thank you for choosing Sa Salem Super Service."
                    )

                    send_sms(courier.sender_phone_num, sms_body)
                    send_sms(courier.receiver_phone_num, sms_body)

                    updated_couriers.append(courier)
            
            serializer = self.get_serializer(updated_couriers, many=True)
            return response.Response(serializer.data, status=status.HTTP_200_OK)
            
        else:
            # Single update (using pk from URL)
            if not pk:
                return response.Response({"error": "courier_ids list or URL pk is required"}, status=status.HTTP_400_BAD_REQUEST)
                
            try:
                courier = Courier.objects.get(pk=pk)
                if courier.status != 'shipping':
                    return response.Response({"error": "Courier is not in 'shipping' status"}, status=status.HTTP_400_BAD_REQUEST)
                    
                if courier.to_location != staff_account.assigned_location:
                    return response.Response({"error": "This courier is not arriving at your assigned location"}, status=status.HTTP_403_FORBIDDEN)
                
                courier.status = 'delevered'
                courier.save()
                
                # Send SMS Notification
                print(f"Sending 'reached' SMS for courier {courier.lr_number}...")
                sms_body = (
                    f"Dear Customer,\n"
                    f"Your parcel has reached the Sa Salem Super Service office successfully.\n"
                    f"LR No: {courier.lr_number}\n"
                    f"From: {courier.from_address}\n"
                    f"To: {courier.to_address}\n"
                    f"You may contact the destination office for delivery or pickup details.\n"
                    f"For support, contact us at +919788321354\n"
                    f"Thank you for choosing Sa Salem Super Service."
                )

                send_sms(courier.sender_phone_num, sms_body)
                send_sms(courier.receiver_phone_num, sms_body)
                
                serializer = self.get_serializer(courier)
                return response.Response(serializer.data, status=status.HTTP_200_OK)
            except Courier.DoesNotExist:
                return response.Response({"error": "Courier not found"}, status=status.HTTP_403_FORBIDDEN)

class RouteCreateView(generics.CreateAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        staff_account = StaffAccount.objects.filter(user=self.request.user).first()
        if staff_account and staff_account.assigned_location:
            serializer.save(from_location=staff_account.assigned_location)
        else:
            # Fallback if no staff account or assigned location (though usually required)
            serializer.save()

class RouteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [permissions.IsAuthenticated]

class RouteListView(generics.ListAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [permissions.IsAuthenticated]

class DriverListView(generics.ListAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [permissions.IsAuthenticated]

class VehicleListView(generics.ListAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

class ReasonListView(generics.ListAPIView):
    queryset = Reason.objects.all()
    serializer_class = ReasonSerializer
    permission_classes = [permissions.IsAuthenticated]


class ExpenseListView(generics.ListCreateAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        staff_account = StaffAccount.objects.filter(user=self.request.user).first()
        if not staff_account:
            return Expense.objects.none()
        return Expense.objects.filter(staff=staff_account).order_by('-created_at')

    def perform_create(self, serializer):
        staff_account = StaffAccount.objects.filter(user=self.request.user).first()
        serializer.save(staff=staff_account)

class AccountDetailView(generics.RetrieveAPIView):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        staff_account = StaffAccount.objects.filter(user=self.request.user).first()
        if not staff_account:
            # This should not happen if user is authenticated and linked
            return None
        
        account, _ = Account.objects.get_or_create(staff=staff_account)
        account.ensure_today()
        account.save() # Recalculate balance and update date
        return account

# class GDMReportView(generics.GenericAPIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         from datetime import datetime

#         date_str = request.query_params.get('date')
#         location_param = request.query_params.get('location')

#         if not date_str:
#             return response.Response(
#                 {"error": "date parameter is required (format: YYYY-MM-DD or DD-MM-YYYY)"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         parsed_date = None
#         for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
#             try:
#                 parsed_date = datetime.strptime(date_str, fmt).date()
#                 break
#             except ValueError:
#                 continue

#         if not parsed_date:
#             return response.Response(
#                 {"error": "Invalid date format. Use YYYY-MM-DD or DD-MM-YYYY"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         queryset = GDM.objects.filter(dispatch_date__date=parsed_date)

#         if location_param:
#             if location_param.isdigit():
#                 queryset = queryset.filter(route__from_location_id=int(location_param))
#             else:
#                 queryset = queryset.filter(route__from_location__name__iexact=location_param)

#         if not queryset.exists():
#             return response.Response(
#                 {"error": "No GDMs found for the specified date and location"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         bookings_data = []
#         total_packages = 0
#         total_freight = 0
#         seen_courier_ids = set()

#         for gdm in queryset:
#             for courier in gdm.couriers.all():
#                 if courier.id in seen_courier_ids:
#                     continue
#                 seen_courier_ids.add(courier.id)

#                 pkgs_count = 0
#                 pkg_name_parts = []
#                 if courier.parcel_information and isinstance(courier.parcel_information, list):
#                     for item in courier.parcel_information:
#                         if isinstance(item, list) and len(item) > 0:
#                             pkg_name_parts.append(str(item[0]))
#                             if len(item) > 1:
#                                 try:
#                                     pkgs_count += int(item[1])
#                                 except (ValueError, TypeError):
#                                     pass

#                 package_name = ", ".join(pkg_name_parts) if pkg_name_parts else "General Parcel"
#                 if not pkgs_count:
#                     pkgs_count = 1

#                 total_packages += pkgs_count
#                 total_freight += courier.total

#                 bookings_data.append({
#                     "lr_no": courier.lr_number or courier.invoice_number,
#                     "payment_mode": courier.payment.mode if courier.payment else "",
#                     "package_name": package_name,
#                     "travellers_count": pkgs_count,
#                     "total_price": courier.total
#                 })

#         gdm_data = {
#             "gdm_no": queryset[0].gdm_number if len(queryset) == 1 else ", ".join(g.gdm_number for g in queryset),
#             "dispatch_date": parsed_date.strftime("%d-%m-%Y"),
#             "route": f"{queryset[0].route.from_location.name} → {queryset[0].route.to_location.name}" if len(queryset) == 1 else "All Routes",
#             "vehicle_no": queryset[0].vehicle_number if len(queryset) == 1 else ", ".join(set(g.vehicle_number for g in queryset)),
#             "driver_name": queryset[0].driver.user_name if len(queryset) == 1 else ", ".join(set(g.driver.user_name for g in queryset)),
#             "total_packages": total_packages,
#             "total_freight": total_freight,
#             "bookings": bookings_data
#         }

#         pdf_buffer = generate_gdm_pdf(gdm_data)
#         response_obj = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
#         response_obj['Access-Control-Expose-Headers'] = 'Content-Disposition'
#         response_obj['Content-Disposition'] = f'attachment; filename="gdm_report_{parsed_date.strftime("%Y-%m-%d")}.pdf"'
#         return response_obj


class GDMPDFView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = GDM.objects.all()

    def get_serializer_class(self):
        return GDMSerializer

    # def get_queryset(self):
    #     staff_account = StaffAccount.objects.filter(user=self.request.user).first()
    #     if not staff_account:
    #         return GDM.objects.none()
    #     return GDM.objects.filter(created_by=staff_account)

    def get(self, request, pk=None, *args, **kwargs):
        gdm_id = pk or request.query_params.get('pk') or request.query_params.get('id') or request.query_params.get('gdm_id')
        if not gdm_id:
            return response.Response(
                {"error": "GDM ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            gdm = self.get_queryset().get(pk=gdm_id)
        except (GDM.DoesNotExist, ValueError):
            return response.Response(
                {"error": "GDM not found or permission denied"},
                status=status.HTTP_404_NOT_FOUND
            )

        bookings_data = []
        total_packages = 0
        total_freight = 0

        for courier in gdm.couriers.all():
            pkgs_count = 0
            pkg_name_parts = []
            if courier.parcel_information and isinstance(courier.parcel_information, list):
                for item in courier.parcel_information:
                    if isinstance(item, list) and len(item) > 0:
                        pkg_name_parts.append(str(item[0]))
                        if len(item) > 1:
                            try:
                                pkgs_count += int(item[1])
                            except (ValueError, TypeError):
                                pass

            package_name = ", ".join(pkg_name_parts) if pkg_name_parts else "General Parcel"
            if not pkgs_count:
                pkgs_count = 1

            total_packages += pkgs_count
            total_freight += courier.total

            bookings_data.append({
                "lr_no": courier.lr_number or courier.invoice_number,
                "payment_mode": courier.payment.mode if courier.payment else "",
                "package_name": package_name,
                "travellers_count": pkgs_count,
                "total_price": courier.total
            })

        gdm_data = {
            "gdm_no": gdm.gdm_number or "",
            "dispatch_date": gdm.dispatch_date.strftime("%d-%m-%Y") if gdm.dispatch_date else "",
            "route": f"{gdm.route.from_location.name} → {gdm.route.to_location.name}" if gdm.route else "No Route",
            "vehicle_no": gdm.vehicle_number or "",
            "driver_name": gdm.driver.user_name if gdm.driver else "",
            "total_packages": total_packages,
            "total_freight": total_freight,
            "bookings": bookings_data
        }

        pdf_buffer = generate_gdm_pdf(gdm_data)
        response_obj = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response_obj['Access-Control-Expose-Headers'] = 'Content-Disposition'
        response_obj['Content-Disposition'] = f'attachment; filename="gdm_{gdm.gdm_number or gdm.id}.pdf"'
        return response_obj

