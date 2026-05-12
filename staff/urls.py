from django.urls import path
from .views import (
    CourierCreateView, OtherLocationListView, RouteCreateView, 
    DriverListView, VehicleListView, RouteDetailView, 
    CourierListView, CourierAssignRouteView, CourierMarkShippingView,
    CourierMarkDeleveredView, RouteListView, CourierDetailView,
    StaffLoginView, GDMCreateView, GDMListView, GDMDetailView,
    DeleveredCourierListView, PaidCourierListView, ToPayCourierListView,
    ReasonListView, ExpenseListView, AccountDetailView
)

urlpatterns = [
    path('login/', StaffLoginView.as_view(), name='staff-login'),
    path('gdms/create/', GDMCreateView.as_view(), name='gdm-create'),
    path('gdms/', GDMListView.as_view(), name='gdm-list'),
    path('gdms/<int:pk>/', GDMDetailView.as_view(), name='gdm-detail'),
    path('couriers/create/', CourierCreateView.as_view(), name='courier-create'),
    path('couriers/<int:pk>/', CourierDetailView.as_view(), name='courier-detail'),
    path('couriers/assign-route/', CourierAssignRouteView.as_view(), name='courier-assign-route'),
    path('couriers/<int:pk>/mark-shipping/', CourierMarkShippingView.as_view(), name='courier-mark-shipping'),
    path('couriers/bulk-mark-shipping/', CourierMarkShippingView.as_view(), name='courier-bulk-mark-shipping'),
    path('couriers/<int:pk>/mark-delevered/', CourierMarkDeleveredView.as_view(), name='courier-mark-delevered'),
    path('couriers/bulk-mark-delevered/', CourierMarkDeleveredView.as_view(), name='courier-bulk-mark-delevered'),
    path('couriers/', CourierListView.as_view(), name='courier-list'),
    path('couriers/delevered-to-customer/', DeleveredCourierListView.as_view(), name='couriers-delevered-to-customer'),
    path('couriers/paid/', PaidCourierListView.as_view(), name='couriers-paid'),
    path('couriers/to-pay/', ToPayCourierListView.as_view(), name='couriers-to-pay'),
    path('locations/other/', OtherLocationListView.as_view(), name='other-locations-list'),
    path('routes/create/', RouteCreateView.as_view(), name='route-create'),
    path('routes/', RouteListView.as_view(), name='route-list'),
    path('routes/<int:pk>/', RouteDetailView.as_view(), name='route-detail'),
    path('drivers/', DriverListView.as_view(), name='driver-list'),
    path('vehicles/', VehicleListView.as_view(), name='vehicle-list'),
    path('reasons/', ReasonListView.as_view(), name='reason-list'),
    path('expenses/', ExpenseListView.as_view(), name='expense-list'),
    path('account/', AccountDetailView.as_view(), name='account-detail'),
]
