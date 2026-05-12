from django.urls import path
from .views import (
    CourierCreateView, OtherLocationListView, RouteCreateView, 
    DriverListView, VehicleListView, RouteDetailView, 
    CourierListView, CourierAssignRouteView, CourierMarkShippingView,
    CourierMarkDeliveredView, RouteListView, CourierDetailView,
    StaffLoginView
)

urlpatterns = [
    path('login/', StaffLoginView.as_view(), name='staff-login'),
    path('couriers/create/', CourierCreateView.as_view(), name='courier-create'),
    path('couriers/<int:pk>/', CourierDetailView.as_view(), name='courier-detail'),
    path('couriers/assign-route/', CourierAssignRouteView.as_view(), name='courier-assign-route'),
    path('couriers/<int:pk>/mark-shipping/', CourierMarkShippingView.as_view(), name='courier-mark-shipping'),
    path('couriers/bulk-mark-shipping/', CourierMarkShippingView.as_view(), name='courier-bulk-mark-shipping'),
    path('couriers/<int:pk>/mark-delivered/', CourierMarkDeliveredView.as_view(), name='courier-mark-delivered'),
    path('couriers/bulk-mark-delivered/', CourierMarkDeliveredView.as_view(), name='courier-bulk-mark-delivered'),
    path('couriers/', CourierListView.as_view(), name='courier-list'),
    path('locations/other/', OtherLocationListView.as_view(), name='other-locations-list'),
    path('routes/create/', RouteCreateView.as_view(), name='route-create'),
    path('routes/', RouteListView.as_view(), name='route-list'),
    path('routes/<int:pk>/', RouteDetailView.as_view(), name='route-detail'),
    path('drivers/', DriverListView.as_view(), name='driver-list'),
    path('vehicles/', VehicleListView.as_view(), name='vehicle-list'),
]
