from rest_framework import generics, permissions
from .serializers import StaffUserSerializer

class CreateStaffUserView(generics.CreateAPIView):
    serializer_class = StaffUserSerializer
    permission_classes = [permissions.IsAdminUser]
