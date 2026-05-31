from rest_framework import generics, permissions, status, response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.pagination import PageNumberPagination
from staff.models import Expense, GDM, StaffAccount, Driver, Vehicle
from .serializers import StaffUserSerializer, AdminExpenseSerializer, DispatchMemoSerializer, StaffListSerializer, DriverListSerializer, DriverCreateSerializer, StaffCreateSerializer, VehicleListSerializer, VehicleCreateSerializer, GDMDetailsSerializer

class CreateStaffUserView(generics.CreateAPIView):
    serializer_class = StaffUserSerializer
    permission_classes = [permissions.IsAdminUser]

class ScrollPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class TotalExpense(generics.ListAPIView):
    serializer_class = AdminExpenseSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    pagination_class = ScrollPagination

    def get_queryset(self):
        # returns the data in descending order(latest first)
        queryset = Expense.objects.all().order_by('-created_at')
        
        # filter of branch (for getting the branch use staff -> assigned_location)
        branch = self.request.query_params.get('branch', 'all')
        if branch and branch.lower() != 'all':
            if branch.isdigit():
                queryset = queryset.filter(staff__assigned_location_id=int(branch))
            else:
                queryset = queryset.filter(staff__assigned_location__name__iexact=branch)
                
        return queryset

class DispatchMemo(generics.ListAPIView):
    queryset = GDM.objects.all().order_by('-dispatch_date')
    serializer_class = DispatchMemoSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

class StaffListView(generics.ListAPIView):
    queryset = StaffAccount.objects.all().order_by('-created_at')
    serializer_class = StaffListSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

class DriverListView(generics.ListAPIView):
    queryset = Driver.objects.all().order_by('id')
    serializer_class = DriverListSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

class DriverCreateView(generics.CreateAPIView):
    serializer_class = DriverCreateSerializer
    permission_classes = [permissions.IsAdminUser]

class StaffCreateView(generics.CreateAPIView):
    serializer_class = StaffCreateSerializer
    permission_classes = [permissions.IsAdminUser]

class VehicleListView(generics.ListAPIView):
    queryset = Vehicle.objects.all().order_by('id')
    serializer_class = VehicleListSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

class VehicleCreateView(generics.CreateAPIView):
    serializer_class = VehicleCreateSerializer
    permission_classes = [permissions.IsAdminUser]

class GDMDetailsListView(generics.ListAPIView):
    serializer_class = GDMDetailsSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get_queryset(self):
        queryset = GDM.objects.all().order_by('-dispatch_date')
        gdm_number = self.request.query_params.get('gdm_number')
        if gdm_number:
            queryset = queryset.filter(gdm_number__iexact=gdm_number)
        return queryset


class AdminLoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return response.Response({"error": "email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = None
        try:
            if '@' in email:
                user_obj = User.objects.get(email=email)
            else:
                user_obj = User.objects.get(username=email)
            
            authenticated_user = authenticate(username=user_obj.username, password=password)
            if authenticated_user:
                user = authenticated_user
        except User.DoesNotExist:
            user = authenticate(username=email, password=password)

        if user:
            if user.is_staff or user.is_superuser:
                refresh = RefreshToken.for_user(user)
                return response.Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'username': user.username,
                    'email': user.email
                }, status=status.HTTP_200_OK)
            else:
                return response.Response({"error": "User is not an administrator"}, status=status.HTTP_403_FORBIDDEN)
        else:
            return response.Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)







