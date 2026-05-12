from django.db.models import Q
from django.contrib.auth import authenticate
from rest_framework import generics, permissions, status, response
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import HttpResponse
from .models import Courier, StaffAccount, Location, Route, Driver, Vehicle, GDM
from .serializers import (
    CourierSerializer, LocationSerializer, RouteSerializer, 
    DriverSerializer, VehicleSerializer, GDMSerializer
)
from .utils import generate_courier_pdf

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
            route=route,
            status='unshipped'
        )
        gdm.couriers.set(couriers)
        gdm.save()
        
        serializer = self.get_serializer(gdm)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

class GDMListView(generics.ListAPIView):
    serializer_class = GDMSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return only GDMs created by the current staff or related to their location if needed
        # For now, let's return all GDMs for simplicity as the user didn't specify filtering
        return GDM.objects.all().order_by('-dispatch_date')

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
        staff_account = StaffAccount.objects.filter(user=self.request.user).first()
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
                Q(status='shipping') | Q(status='inplace'),
                to_location=assigned_location
            )
        elif status_filter == 'recieved':
            return queryset.filter(status='delevered', to_location=assigned_location)
        else: # 'all' or any other value
            return queryset.filter(
                Q(from_location=assigned_location) | Q(to_location=assigned_location)
            )

class CourierDetailView(generics.RetrieveAPIView):
    queryset = Courier.objects.all()
    serializer_class = CourierSerializer
    permission_classes = [permissions.IsAuthenticated]

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

        # Generate PDF
        pdf_buffer = generate_courier_pdf(courier)
        
        # Return PDF response
        response_obj = HttpResponse(pdf_buffer, content_type='application/pdf', status=status.HTTP_201_CREATED)
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
            courier.status = 'shipping'
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
                
                courier.status = 'shipping'
                courier.save()
                
                serializer = self.get_serializer(courier)
                return response.Response(serializer.data, status=status.HTTP_200_OK)
            except Courier.DoesNotExist:
                return response.Response({"error": "Courier not found"}, status=status.HTTP_404_NOT_FOUND)

class CourierMarkDeliveredView(generics.GenericAPIView):
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
                
                serializer = self.get_serializer(courier)
                return response.Response(serializer.data, status=status.HTTP_200_OK)
            except Courier.DoesNotExist:
                return response.Response({"error": "Courier not found"}, status=status.HTTP_404_NOT_FOUND)

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
