from django.urls import path
from .views import CreateStaffUserView, TotalExpense, DispatchMemo, StaffListView, DriverListView, DriverCreateView, StaffCreateView, VehicleListView, VehicleCreateView, GDMDetailsListView

urlpatterns = [
    path('staff/create/', StaffCreateView.as_view(), name='create-staff-user'),
    path('staff/', StaffListView.as_view(), name='staff-list'),
    path('expenses/', TotalExpense.as_view(), name='total-expenses'),
    path('dispatch-memo/', DispatchMemo.as_view(), name='dispatch-memo'),
    path('drivers/', DriverListView.as_view(), name='driver-list-admin'),
    path('drivers/create/', DriverCreateView.as_view(), name='driver-create-admin'),
    path('vehicles/', VehicleListView.as_view(), name='vehicle-list-admin'),
    path('vehicles/create/', VehicleCreateView.as_view(), name='vehicle-create-admin'),
    path('gdm-details/', GDMDetailsListView.as_view(), name='gdm-details-admin'),
]