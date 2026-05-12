from django.urls import path
from .views import CreateStaffUserView

urlpatterns = [
    path('staff/create/', CreateStaffUserView.as_view(), name='create-staff-user'),
]
