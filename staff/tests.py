from django.test import TestCase
from django.contrib.auth.models import User
from .models import Location, StaffAccount, Courier, Payment, Driver, Route, Vehicle, GDM

class RouteModelTest(TestCase):
    def setUp(self):
        self.loc1 = Location.objects.create(name="Point A", short_code="PA")
        self.loc2 = Location.objects.create(name="Point B", short_code="PB")
        self.loc3 = Location.objects.create(name="Point C", short_code="PC")
        self.user = User.objects.create_user(username="driveruser", password="password")
        self.driver = Driver.objects.create(user_name="driveruser", license_number="LIC123")
        self.vehicle = Vehicle.objects.create(vehicle_number="V123")

    def test_route_creation(self):
        route = Route.objects.create(
            from_location=self.loc1,
            to_location=self.loc3,
            route_path=["Point B"],
            driver=self.driver,
            vehicle=self.vehicle
        )
        self.assertEqual(route.from_location.name, "Point A")
        self.assertEqual(route.to_location.name, "Point C")
        self.assertEqual(route.route_path[0], "Point B")
        self.assertEqual(route.driver.license_number, "LIC123")

class CourierModelTest(TestCase):
    def setUp(self):
        self.location1 = Location.objects.create(name="New York", short_code="NY")
        self.location2 = Location.objects.create(name="Los Angeles", short_code="LA")
        self.user = User.objects.create_user(username="staffuser", password="password")
        self.staff = StaffAccount.objects.create(user=self.user, assigned_location=self.location1)
        self.payment = Payment.objects.create(amount=1000, status='Paid', mode='Cash')

    def test_courier_creation_and_total_property(self):
        courier = Courier.objects.create(
            created_by=self.staff,
            from_location=self.location1,
            to_location=self.location2,
            sender_name="John Doe",
            receiver_name="Jane Smith",
            from_address="123 Main St, NY",
            to_address="456 Elm St, LA",
            sender_phone_num="1234567890",
            receiver_phone_num="0987654321",
            parcel_information=[["Electronics", 2], ["Books", 5]],
            weight=10,
            payment=self.payment,
            invoice_number="INV-001",
            freight=500,
            loading_unloading=50,
            door_pickup=100,
            other_transport_crossing=20,
            mamool=30,
            statistical_charges=10,
            door_delivery=80,
            delivery_type="Door Delivery"
        )
        
        self.assertEqual(courier.sender_name, "John Doe")
        self.assertEqual(courier.total, 500 + 50 + 100 + 20 + 30 + 10 + 80)
        self.assertEqual(courier.total, 790)
        self.assertEqual(courier.delivery_type, "Door Delivery")
        self.assertEqual(courier.parcel_information[0][0], "Electronics")

    def test_courier_str(self):
        courier = Courier.objects.create(
            created_by=self.staff,
            from_location=self.location1,
            to_location=self.location2,
            sender_name="John Doe",
            receiver_name="Jane Smith",
            from_address="123 Main St, NY",
            to_address="456 Elm St, LA",
            sender_phone_num="1234567890",
            receiver_phone_num="0987654321",
            parcel_information=[["nature1", 1]],
            weight=5,
            invoice_number="INV-002",
            delivery_type="GoodDown Delivery"
        )
        self.assertEqual(str(courier), f"Courier {courier.lr_number} - John Doe to Jane Smith")

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class CourierAPITest(APITestCase):
    def setUp(self):
        self.location1 = Location.objects.create(name="New York", short_code="NY")
        self.location2 = Location.objects.create(name="Los Angeles", short_code="LA")
        self.user = User.objects.create_user(username="apiuser", password="password")
        self.staff = StaffAccount.objects.create(user=self.user, assigned_location=self.location1)
        self.client.force_authenticate(user=self.user)
        self.url = reverse('courier-create')

    def test_staff_login(self):
        # We need to test without force_authenticate
        self.client.force_authenticate(user=None)
        url = reverse('staff-login')
        data = {
            "staffID": self.staff.staffID,
            "password": "password"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['staffID'], self.staff.staffID)

    def test_create_courier_api(self):
        data = {
            "to_location": self.location2.id,
            "sender_name": "Alice",
            "receiver_name": "Bob",
            "from_address": "NY Address",
            "to_address": "LA Address",
            "sender_phone_num": "1111111111",
            "receiver_phone_num": "2222222222",
            "parcel_information": [["Gifts", 3]],
            "weight": 2,
            "invoice_number": "INV-API-001",
            "freight": 200,
            "loading_unloading": 20,
            "door_pickup": 30,
            "delivery_type": "Door Delivery",
            "payment_status": "Paid",
            "payment_mode": "Online"
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        
        courier = Courier.objects.get(invoice_number="INV-API-001")
        self.assertEqual(courier.created_by, self.staff)
        self.assertEqual(courier.from_location, self.location1)
        self.assertEqual(courier.lr_number, f"LR-NY-{courier.id}")
        self.assertEqual(courier.status, "inplace")
        self.assertFalse(courier.delevered_to_customer)
        self.assertEqual(courier.payment.amount, 250)
        self.assertEqual(courier.payment.status, "Paid")
        self.assertEqual(courier.payment.mode, "Online")

    def test_list_couriers_filtered_by_status(self):
        # Setup different couriers
        # 1. Inplace at loc1
        Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            status='inplace', invoice_number="INP1", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        # 2. Shipping from loc1
        Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            status='shipping', invoice_number="SHIP1", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        # 3. delevered from loc1 (Sent)
        Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            status='delevered', invoice_number="SENT1", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        # 4. Inplace/Shipping to loc1 (Incoming)
        Courier.objects.create(
            created_by=self.staff, from_location=self.location2, to_location=self.location1,
            status='shipping', invoice_number="INC1", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        # 5. delevered to loc1 (Received)
        Courier.objects.create(
            created_by=self.staff, from_location=self.location2, to_location=self.location1,
            status='delevered', invoice_number="REC1", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        # 6. Inplace to loc1 (Should be EXCLUDED from 'all')
        Courier.objects.create(
            created_by=self.staff, from_location=self.location2, to_location=self.location1,
            status='inplace', invoice_number="INC_INP1", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )

        base_url = reverse('courier-list')

        # Test 'inplace'
        response = self.client.get(f"{base_url}?status=inplace")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['invoice_number'], "INP1")

        # Test 'shipping'
        response = self.client.get(f"{base_url}?status=shipping")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['invoice_number'], "SHIP1")

        # Test 'sent'
        response = self.client.get(f"{base_url}?status=sent")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['invoice_number'], "SENT1")

        # Test 'incoming'
        response = self.client.get(f"{base_url}?status=incoming")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['invoice_number'], "INC1")

        # Test 'recieved'
        response = self.client.get(f"{base_url}?status=recieved")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['invoice_number'], "REC1")

        # Test 'all' (default)
        response = self.client.get(base_url)
        self.assertEqual(len(response.data), 5) # Should NOT include INC_INP1

    def test_assign_route(self):
        courier = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            sender_name="S", receiver_name="R", weight=1, invoice_number="INV1", parcel_information=[], delivery_type="Door Delivery"
        )
        route = Route.objects.create(
            from_location=self.location1, to_location=self.location2, route_path=[],
            driver=Driver.objects.create(user_name="dr", license_number="L"),
            vehicle=Vehicle.objects.create(vehicle_number="V")
        )
        
        url = reverse('courier-assign-route')
        data = {"courier_id": courier.id, "route_id": route.id}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        courier.refresh_from_db()
        self.assertEqual(courier.route, route)
        self.assertEqual(courier.vehicle, route.vehicle)
        self.assertEqual(courier.status, 'inplace') # User commented out shipping status update in views.py

    def test_mark_shipping(self):
        route = Route.objects.create(
            from_location=self.location1, to_location=self.location2, route_path=[],
            driver=Driver.objects.create(user_name="dr_sh", license_number="L_SH"),
            vehicle=Vehicle.objects.create(vehicle_number="V_SH")
        )
        courier = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            status='inplace', invoice_number="INV_SH1", parcel_information=[], weight=1, 
            delivery_type="Door Delivery", route=route
        )
        url = reverse('courier-mark-shipping', kwargs={'pk': courier.pk})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        courier.refresh_from_db()
        self.assertEqual(courier.status, 'shipping')

    def test_mark_shipping_no_route(self):
        courier = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            status='inplace', invoice_number="INV_SH_NO", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        url = reverse('courier-mark-shipping', kwargs={'pk': courier.pk})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Courier does not have an assigned route")

    def test_mark_shipping_invalid_location(self):
        loc3 = Location.objects.create(name="Chicago", short_code="CH")
        courier = Courier.objects.create(
            created_by=self.staff, from_location=loc3, to_location=self.location2,
            status='inplace', invoice_number="INV_SH2", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        url = reverse('courier-mark-shipping', kwargs={'pk': courier.pk})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bulk_mark_shipping(self):
        route = Route.objects.create(
            from_location=self.location1, to_location=self.location2, route_path=[],
            driver=Driver.objects.create(user_name="dr_bulk", license_number="L_BULK"),
            vehicle=Vehicle.objects.create(vehicle_number="V_BULK")
        )
        c1 = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            status='inplace', invoice_number="B1", parcel_information=[], weight=1, delivery_type="Door Delivery",
            route=route
        )
        c2 = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            status='inplace', invoice_number="B2", parcel_information=[], weight=1, delivery_type="Door Delivery",
            route=route
        )
        c3 = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            status='shipping', invoice_number="B3", parcel_information=[], weight=1, delivery_type="Door Delivery",
            route=route
        )
        
        url = reverse('courier-bulk-mark-shipping')
        data = {"courier_ids": [c1.id, c2.id, c3.id]}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only B1 and B2 should be updated
        
        c1.refresh_from_db()
        self.assertEqual(c1.status, 'shipping')
        c3.refresh_from_db()
        self.assertEqual(c3.status, 'shipping') # Was already shipping

    def test_bulk_mark_shipping_no_route(self):
        c1 = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            status='inplace', invoice_number="B1_NO", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        url = reverse('courier-bulk-mark-shipping')
        data = {"courier_ids": [c1.id]}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("does not have an assigned route", response.data['error'])

    def test_mark_delevered(self):
        # Courier is shipping to location1 (staff's location)
        courier = Courier.objects.create(
            created_by=self.staff, from_location=self.location2, to_location=self.location1,
            status='shipping', invoice_number="INV_DEL1", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        url = reverse('courier-mark-delevered', kwargs={'pk': courier.pk})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        courier.refresh_from_db()
        self.assertEqual(courier.status, 'delevered')

    def test_mark_delevered_invalid_location(self):
        # Courier is shipping to location2 (not staff's location)
        courier = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            status='shipping', invoice_number="INV_DEL2", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        url = reverse('courier-mark-delevered', kwargs={'pk': courier.pk})
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bulk_mark_delevered(self):
        c1 = Courier.objects.create(
            created_by=self.staff, from_location=self.location2, to_location=self.location1,
            status='shipping', invoice_number="BD1", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        c2 = Courier.objects.create(
            created_by=self.staff, from_location=self.location2, to_location=self.location1,
            status='shipping', invoice_number="BD2", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        c3 = Courier.objects.create(
            created_by=self.staff, from_location=self.location2, to_location=self.location1,
            status='inplace', invoice_number="BD3", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        
        url = reverse('courier-bulk-mark-delevered')
        data = {"courier_ids": [c1.id, c2.id, c3.id]}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only BD1 and BD2 should be updated
        
        c1.refresh_from_db()
        self.assertEqual(c1.status, 'delevered')
        c3.refresh_from_db()
        self.assertEqual(c3.status, 'inplace') # Remained inplace

    def test_retrieve_courier(self):
        courier = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            sender_name="Alice", receiver_name="Bob", weight=5, invoice_number="RET1", parcel_information=[], delivery_type="Door Delivery"
        )
        url = reverse('courier-detail', kwargs={'pk': courier.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['invoice_number'], "RET1")
        self.assertEqual(response.data['sender_name'], "Alice")

    def test_create_gdm_api(self):
        # Setup route, vehicle, driver
        driver = Driver.objects.create(user_name="gdmdr", license_number="L_GDM")
        vehicle = Vehicle.objects.create(vehicle_number="V_GDM")
        route = Route.objects.create(from_location=self.location1, to_location=self.location2, route_path=[], driver=driver, vehicle=vehicle)
        
        # Create couriers with same route and vehicle
        c1 = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            route=route, vehicle=vehicle, invoice_number="G1", parcel_information=[], weight=10, delivery_type="Door Delivery"
        )
        c2 = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            route=route, vehicle=vehicle, invoice_number="G2", parcel_information=[], weight=5, delivery_type="Door Delivery"
        )
        
        url = reverse('gdm-create')
        data = {"couriers": [c1.id, c2.id]}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['vehicle_number'], "V_GDM")
        self.assertEqual(response.data['total_weights'], 15)
        self.assertEqual(response.data['total_couriers_count'], 2)

    def test_create_gdm_mismatch(self):
        # Setup 2 different routes
        driver = Driver.objects.create(user_name="gdmdr2", license_number="L_GDM2")
        vehicle = Vehicle.objects.create(vehicle_number="V_GDM2")
        route1 = Route.objects.create(from_location=self.location1, to_location=self.location2, route_path=[], driver=driver, vehicle=vehicle)
        route2 = Route.objects.create(from_location=self.location1, to_location=self.location2, route_path=["Stop"], driver=driver, vehicle=vehicle)
        
        c1 = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            route=route1, vehicle=vehicle, invoice_number="GM1", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        c2 = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            route=route2, vehicle=vehicle, invoice_number="GM2", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        
        url = reverse('gdm-create')
        data = {"couriers": [c1.id, c2.id]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "All couriers must belong to the same route")

    def test_list_gdm_api(self):
        # Setup
        driver = Driver.objects.create(user_name="gdmlistdr", license_number="L_GDML")
        vehicle = Vehicle.objects.create(vehicle_number="V_GDML")
        route = Route.objects.create(from_location=self.location1, to_location=self.location2, route_path=["Midway"], driver=driver, vehicle=vehicle)
        
        gdm = GDM.objects.create(
            created_by=self.staff, vehicle_number="V_GDML", driver=driver, route=route
        )
        
        url = reverse('gdm-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['gdm_number'], gdm.gdm_number)
        self.assertEqual(response.data[0]['all_locations'], ["New York", "Midway", "Los Angeles"])
    def test_list_gdm_filtering(self):
        # Create another staff and GDM
        other_user = User.objects.create_user(username="otherstaff", password="password")
        other_staff = StaffAccount.objects.create(user=other_user, assigned_location=self.location1)
        driver = Driver.objects.create(user_name="dr2", license_number="L2")
        vehicle = Vehicle.objects.create(vehicle_number="V2")
        route = Route.objects.create(from_location=self.location1, to_location=self.location2, route_path=[], driver=driver, vehicle=vehicle)
        
        GDM.objects.create(
            created_by=other_staff, vehicle_number="V2", driver=driver, route=route
        )
        
        # Current staff (self.user) should see 0 GDMs initially
        url = reverse('gdm-list')
        response = self.client.get(url)
        self.assertEqual(len(response.data), 0)
        
        # Create one for current staff
        GDM.objects.create(
            created_by=self.staff, vehicle_number="V1", driver=driver, route=route
        )
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

    def test_gdm_status_property(self):
        driver = Driver.objects.create(user_name="d_status", license_number="L_STATUS")
        vehicle = Vehicle.objects.create(vehicle_number="V_STATUS")
        route = Route.objects.create(from_location=self.location1, to_location=self.location2, route_path=[], driver=driver, vehicle=vehicle)
        
        c1 = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            status='inplace', invoice_number="C1_S", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        c2 = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            status='delevered', invoice_number="C2_S", parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        
        gdm = GDM.objects.create(created_by=self.staff, vehicle_number="V_STATUS", driver=driver, route=route)
        gdm.couriers.set([c1, c2])
        
        # 1 inplace, 1 delevered -> "inplace"
        self.assertEqual(gdm.status, "inplace")
        
        # Change c1 to shipping. 1 shipping, 1 delevered -> "shipping"
        c1.status = 'shipping'
        c1.save()
        self.assertEqual(gdm.status, "shipping")
        
        # Change c1 to delevered. All delevered -> "sent"
        c1.status = 'delevered'
        c1.save()
        self.assertEqual(gdm.status, "sent")
        
        # Empty couriers -> unshipped
        gdm.couriers.clear()
        self.assertEqual(gdm.status, "unshipped")

    def test_update_gdm_api(self):
        driver = Driver.objects.create(user_name="updr", license_number="LU")
        vehicle = Vehicle.objects.create(vehicle_number="VU")
        route = Route.objects.create(from_location=self.location1, to_location=self.location2, route_path=[], driver=driver, vehicle=vehicle)
        gdm = GDM.objects.create(created_by=self.staff, vehicle_number="OLD_V", driver=driver, route=route)
        
        url = reverse('gdm-detail', kwargs={'pk': gdm.pk})
        data = {"vehicle_number": "NEW_V"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        gdm.refresh_from_db()
        self.assertEqual(gdm.vehicle_number, "NEW_V")

    def test_delete_gdm_api(self):
        driver = Driver.objects.create(user_name="deldr", license_number="LD")
        vehicle = Vehicle.objects.create(vehicle_number="VD")
        route = Route.objects.create(from_location=self.location1, to_location=self.location2, route_path=[], driver=driver, vehicle=vehicle)
        gdm = GDM.objects.create(created_by=self.staff, vehicle_number="VD", driver=driver, route=route)
        
        url = reverse('gdm-detail', kwargs={'pk': gdm.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(GDM.objects.count(), 0)

    def test_gdm_permissions(self):
        # Create GDM by another staff
        other_user = User.objects.create_user(username="otherstaff2", password="password")
        other_staff = StaffAccount.objects.create(user=other_user, assigned_location=self.location1)
        driver = Driver.objects.create(user_name="dr3", license_number="L3")
        vehicle = Vehicle.objects.create(vehicle_number="V3")
        route = Route.objects.create(from_location=self.location1, to_location=self.location2, route_path=[], driver=driver, vehicle=vehicle)
        gdm = GDM.objects.create(created_by=other_staff, vehicle_number="V3", driver=driver, route=route)
        
        # Authenticated as self.user, try to access other_staff's GDM
        url = reverse('gdm-detail', kwargs={'pk': gdm.pk})
        
        # GET should be 404 because get_queryset filters it out
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # PATCH should be 404
        response = self.client.patch(url, {"vehicle_number": "HACKED"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # DELETE should be 404
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_other_locations(self):
        url = reverse('other-locations-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should contain location2 but not location1 (assigned)
        location_names = [loc['name'] for loc in response.data]
        self.assertIn("Los Angeles", location_names)
        self.assertNotIn("New York", location_names)

    def test_delevered_courier_list(self):
        url = reverse('couriers-delevered-to-customer')
        
        # 1. Meets all conditions
        c1 = Courier.objects.create(
            created_by=self.staff, from_location=self.location2, to_location=self.location1,
            status='delevered', delevered_to_customer=True, invoice_number="C1", 
            parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        
        # 2. delevered_to_customer=False
        c2 = Courier.objects.create(
            created_by=self.staff, from_location=self.location2, to_location=self.location1,
            status='delevered', delevered_to_customer=False, invoice_number="C2", 
            parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        
        # 3. different to_location
        c3 = Courier.objects.create(
            created_by=self.staff, from_location=self.location1, to_location=self.location2,
            status='delevered', delevered_to_customer=True, invoice_number="C3", 
            parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        
        # 4. different status
        c4 = Courier.objects.create(
            created_by=self.staff, from_location=self.location2, to_location=self.location1,
            status='shipping', delevered_to_customer=True, invoice_number="C4", 
            parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['invoice_number'], "C1")

    def test_paid_and_topay_courier_lists(self):
        # 1. Paid Courier
        p1 = Payment.objects.create(amount=100, status='Paid', mode='Cash')
        c1 = Courier.objects.create(
            created_by=self.staff, from_location=self.location2, to_location=self.location1,
            status='delevered', delevered_to_customer=False, payment=p1, invoice_number="PAID1",
            parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        
        # 2. To Pay Courier
        p2 = Payment.objects.create(amount=100, status='To Pay', mode='None')
        c2 = Courier.objects.create(
            created_by=self.staff, from_location=self.location2, to_location=self.location1,
            status='delevered', delevered_to_customer=False, payment=p2, invoice_number="TOPAY1",
            parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        
        # 3. Delevered to customer (should be excluded from both)
        p3 = Payment.objects.create(amount=100, status='Paid', mode='Cash')
        c3 = Courier.objects.create(
            created_by=self.staff, from_location=self.location2, to_location=self.location1,
            status='delevered', delevered_to_customer=True, payment=p3, invoice_number="DELIV1",
            parcel_information=[], weight=1, delivery_type="Door Delivery"
        )
        
        # Test Paid list
        url_paid = reverse('couriers-paid')
        response = self.client.get(url_paid)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['invoice_number'], "PAID1")
        
        # Test To Pay list
        url_topay = reverse('couriers-to-pay')
        response = self.client.get(url_topay)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['invoice_number'], "TOPAY1")

class RouteAPITest(APITestCase):
    def setUp(self):
        self.loc1 = Location.objects.create(name="Point A", short_code="PA")
        self.loc2 = Location.objects.create(name="Point B", short_code="PB")
        self.loc3 = Location.objects.create(name="Point C", short_code="PC")
        self.user = User.objects.create_user(username="api_driver", password="password")
        self.driver = Driver.objects.create(user_name="apiuser", license_number="API-LIC")
        self.vehicle = Vehicle.objects.create(vehicle_number="V-API")
        self.staff_user = User.objects.create_user(username="staff_api", password="password")
        StaffAccount.objects.create(user=self.staff_user, assigned_location=self.loc1)
        self.client.force_authenticate(user=self.staff_user)
        self.url = reverse('route-create')

    def test_create_route_api(self):
        data = {
            "from_location": self.loc1.id,
            "to_location": self.loc3.id,
            "route_path": [{"id": self.loc2.id, "name": "Point B"}],
            "driver": self.driver.id,
            "vehicle": self.vehicle.id
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        route = Route.objects.get(from_location=self.loc1, to_location=self.loc3)
        self.assertEqual(len(route.route_path), 1)
        self.assertEqual(route.route_path[0]['name'], "Point B")

    def test_update_route_api(self):
        route = Route.objects.create(
            from_location=self.loc1,
            to_location=self.loc3,
            route_path=[],
            driver=self.driver,
            vehicle=self.vehicle
        )
        url = reverse('route-detail', kwargs={'pk': route.pk})
        data = {"route_path": [{"id": self.loc2.id, "name": "Stop 1"}]}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        route.refresh_from_db()
        self.assertEqual(len(route.route_path), 1)

    def test_delete_route_api(self):
        route = Route.objects.create(
            from_location=self.loc1,
            to_location=self.loc3,
            route_path=[],
            driver=self.driver,
            vehicle=self.vehicle
        )
        url = reverse('route-detail', kwargs={'pk': route.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Route.objects.count(), 0)

    def test_list_routes_api(self):
        Route.objects.create(
            from_location=self.loc1, to_location=self.loc3, route_path=[],
            driver=self.driver, vehicle=self.vehicle
        )
        url = reverse('route-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

class DriverVehicleListTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.force_authenticate(user=self.user)
        
        # Create some drivers and vehicles
        Driver.objects.create(user_name="d1", license_number="L1")
        Driver.objects.create(user_name="d2", license_number="L2")
        Vehicle.objects.create(vehicle_number="V1")
        Vehicle.objects.create(vehicle_number="V2")

    def test_list_drivers(self):
        url = reverse('driver-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_vehicles(self):
        url = reverse('vehicle-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
