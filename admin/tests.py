from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from staff.models import Location, StaffAccount, Reason, Expense, GDM, Driver, Route, Vehicle, Courier, Payment

class TotalExpenseAPITest(APITestCase):
    def setUp(self):
        # Create Locations (Branches)
        self.chennai = Location.objects.create(name="Chennai", short_code="CHN")
        self.salem = Location.objects.create(name="Salem", short_code="SLM")

        # Create Users
        self.admin_user = User.objects.create_superuser(username="admin", password="adminpassword", is_staff=True)
        self.staff_user1 = User.objects.create_user(username="staff1", password="staffpassword")
        self.staff_user2 = User.objects.create_user(username="staff2", password="staffpassword")

        # Create StaffAccounts linked to Locations
        self.staff_account1 = StaffAccount.objects.create(user=self.staff_user1, assigned_location=self.chennai)
        self.staff_account2 = StaffAccount.objects.create(user=self.staff_user2, assigned_location=self.salem)

        # Create Reason for expenses
        self.reason = Reason.objects.create(name="Fuel")

        # Create Expenses with delay or distinct times
        self.expense1 = Expense.objects.create(reason=self.reason, staff=self.staff_account1, text="Chennai Fuel Expense", amount=1000)
        self.expense2 = Expense.objects.create(reason=self.reason, staff=self.staff_account2, text="Salem Fuel Expense", amount=1500)
        self.expense3 = Expense.objects.create(reason=self.reason, staff=self.staff_account1, text="Chennai Office Expense", amount=500)

        self.url = reverse('total-expenses')

    def test_anonymous_access_denied(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_access_denied(self):
        self.client.force_authenticate(user=self.staff_user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access_allowed(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_descending_order_and_pagination(self):
        self.client.force_authenticate(user=self.admin_user)
        # Fetch with page_size=2 to test scroll pagination
        response = self.client.get(self.url, {'page_size': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # We expect a paginated response
        data = response.json()
        self.assertIn('count', data)
        self.assertIn('next', data)
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 2)
        
        # Verify descending order (latest first): expense3 should be first, then expense2, then expense1
        results = data['results']
        self.assertEqual(results[0]['id'], self.expense3.id)
        self.assertEqual(results[1]['id'], self.expense2.id)

    def test_filter_by_branch_name(self):
        self.client.force_authenticate(user=self.admin_user)
        
        # Filter by Chennai
        response = self.client.get(self.url, {'branch': 'Chennai'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data['results']
        
        # Chennai should only have expense3 and expense1
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], self.expense3.id)
        self.assertEqual(results[1]['id'], self.expense1.id)

        # Filter by Salem
        response = self.client.get(self.url, {'branch': 'Salem'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data['results']
        
        # Salem should only have expense2
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.expense2.id)

    def test_filter_by_branch_id(self):
        self.client.force_authenticate(user=self.admin_user)
        
        # Filter by Chennai ID
        response = self.client.get(self.url, {'branch': str(self.chennai.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data['results']
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], self.expense3.id)
        self.assertEqual(results[1]['id'], self.expense1.id)

class DispatchMemoAPITest(APITestCase):
    def setUp(self):
        # Create Locations
        self.chennai = Location.objects.create(name="Chennai", short_code="CHN")
        self.salem = Location.objects.create(name="Salem", short_code="SLM")
        
        # Create Driver, Vehicle, Route
        self.driver = Driver.objects.create(user_name="driver1", license_number="LIC123")
        self.vehicle = Vehicle.objects.create(vehicle_number="TN-01-AB-1234")
        self.route = Route.objects.create(
            from_location=self.chennai,
            to_location=self.salem,
            route_path=["Vellore"],
            driver=self.driver,
            vehicle=self.vehicle
        )
        
        # Create Users and StaffAccounts
        self.admin_user = User.objects.create_superuser(username="admin", password="adminpassword", is_staff=True)
        self.staff_user = User.objects.create_user(username="staff", password="staffpassword")
        self.staff_account = StaffAccount.objects.create(user=self.staff_user, assigned_location=self.chennai)
        
        # Create GDM
        self.gdm = GDM.objects.create(
            vehicle_number=self.vehicle.vehicle_number,
            driver=self.driver,
            route=self.route,
            created_by=self.staff_account
        )
        
        # Create Couriers (LRs)
        self.payment1 = Payment.objects.create(amount=100)
        self.payment2 = Payment.objects.create(amount=100)
        self.courier1 = Courier.objects.create(
            created_by=self.staff_account,
            from_location=self.chennai,
            to_location=self.salem,
            sender_name="Alice",
            receiver_name="Bob",
            sender_phone_num="1234567890",
            receiver_phone_num="0987654321",
            parcel_information=[["Docs", 1]],
            weight=2,
            payment=self.payment1,
            freight=500,
            delivery_type="Door Delivery"
        )
        self.courier2 = Courier.objects.create(
            created_by=self.staff_account,
            from_location=self.chennai,
            to_location=self.salem,
            sender_name="Charlie",
            receiver_name="Dave",
            sender_phone_num="1234567890",
            receiver_phone_num="0987654321",
            parcel_information=[["Box", 1]],
            weight=5,
            payment=self.payment2,
            freight=700,
            delivery_type="GoodDown Delivery"
        )
        
        # Associate couriers with GDM
        self.gdm.couriers.set([self.courier1, self.courier2])
        self.gdm.save()
        
        self.url = reverse('dispatch-memo')

    def test_anonymous_access_denied(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_access_denied(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access_allowed_and_correct_data(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Since it is a ListAPIView, we expect results
        # Depending on whether pagination is enabled globally or locally (it is a standard ListAPIView, so it uses default DRF response or paginated if set)
        # Let's check results or direct array
        if isinstance(data, dict) and 'results' in data:
            results = data['results']
        else:
            results = data
            
        self.assertEqual(len(results), 1)
        gdm_details = results[0]
        
        # Check matching details
        self.assertEqual(gdm_details['gdm_number'], self.gdm.gdm_number)
        self.assertEqual(gdm_details['vehicle_number'], "TN-01-AB-1234")
        self.assertEqual(gdm_details['driver'], "driver1")
        
        # Route should be list in proper order: ["Chennai", "Vellore", "Salem"]
        self.assertEqual(gdm_details['route'], ["Chennai", "Vellore", "Salem"])
        
        # Total LRs count: 2
        self.assertEqual(gdm_details['lrs'], 2)
        
        # Freight sum of all couriers: 500 + 700 = 1200
        self.assertEqual(gdm_details['freight'], 1200)

class StaffListAPITest(APITestCase):
    def setUp(self):
        # Create Locations
        self.chennai = Location.objects.create(name="Chennai", short_code="CHN")
        self.salem = Location.objects.create(name="Salem", short_code="SLM")
        
        # Create Users
        self.admin_user = User.objects.create_superuser(username="admin", password="adminpassword", is_staff=True)
        self.staff_user1 = User.objects.create_user(username="staff1", password="staffpassword", first_name="Kumar", last_name="Swamy")
        self.staff_user2 = User.objects.create_user(username="staff2", password="staffpassword", first_name="Vijay", last_name="Kumar")
        
        # Create StaffAccounts
        self.staff_account1 = StaffAccount.objects.create(user=self.staff_user1, assigned_location=self.chennai, status="active")
        self.staff_account2 = StaffAccount.objects.create(user=self.staff_user2, assigned_location=self.salem, status="inactive")
        
        self.url = reverse('staff-list')

    def test_anonymous_access_denied(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_access_denied(self):
        self.client.force_authenticate(user=self.staff_user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access_allowed_and_correct_data(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        if isinstance(data, dict) and 'results' in data:
            results = data['results']
        else:
            results = data
            
        self.assertEqual(len(results), 2)
        
        # staff_account2 is created last, so it should be first in descending order of created_at
        first_item = results[0]
        self.assertEqual(first_item['id'], self.staff_account2.id)
        self.assertEqual(first_item['staff_id'], self.staff_account2.staffID)
        self.assertEqual(first_item['name'], "Vijay Kumar")
        self.assertEqual(first_item['email'], self.staff_user2.email)
        self.assertEqual(first_item['assigned_location'], "Salem")
        self.assertEqual(first_item['status'], "inactive")
        
        second_item = results[1]
        self.assertEqual(second_item['id'], self.staff_account1.id)
        self.assertEqual(second_item['staff_id'], self.staff_account1.staffID)
        self.assertEqual(second_item['name'], "Kumar Swamy")
        self.assertEqual(second_item['email'], self.staff_user1.email)
        self.assertEqual(second_item['assigned_location'], "Chennai")
        self.assertEqual(second_item['status'], "active")

class DriverListAPITest(APITestCase):
    def setUp(self):
        # Create Drivers
        self.driver1 = Driver.objects.create(user_name="driver1", license_number="LIC123", phone_number="9876543210")
        self.driver2 = Driver.objects.create(user_name="driver2", license_number="LIC456", phone_number="9876543211")
        
        # Create Users
        self.admin_user = User.objects.create_superuser(username="admin", password="adminpassword", is_staff=True)
        self.staff_user = User.objects.create_user(username="staff", password="staffpassword")
        
        self.url = reverse('driver-list-admin')

    def test_anonymous_access_denied(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_access_denied(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access_allowed_and_correct_data(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        if isinstance(data, dict) and 'results' in data:
            results = data['results']
        else:
            results = data
            
        self.assertEqual(len(results), 2)
        
        first_item = results[0]
        self.assertEqual(first_item['driver_id'], self.driver1.id)
        self.assertEqual(first_item['name'], "driver1")
        self.assertEqual(first_item['phone_num'], "9876543210")
        self.assertEqual(first_item['status'], "active")

        second_item = results[1]
        self.assertEqual(second_item['driver_id'], self.driver2.id)
        self.assertEqual(second_item['name'], "driver2")
        self.assertEqual(second_item['phone_num'], "9876543211")
        self.assertEqual(second_item['status'], "active")

class DriverCreateAPITest(APITestCase):
    def setUp(self):
        # Create Users
        self.admin_user = User.objects.create_superuser(username="admin", password="adminpassword", is_staff=True)
        self.staff_user = User.objects.create_user(username="staff", password="staffpassword")
        
        self.url = reverse('driver-create-admin')

    def test_anonymous_access_denied(self):
        response = self.client.post(self.url, {'name': 'John Doe', 'phone_number': '9876543212'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_access_denied(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.url, {'name': 'John Doe', 'phone_number': '9876543212'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access_allowed_and_creates_account_and_driver(self):
        self.client.force_authenticate(user=self.admin_user)
        
        payload = {
            'name': 'John Doe',
            'phone_number': '9876543212'
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        data = response.json()
        
        # Verify response structure matches DriverListSerializer
        self.assertIn('driver_id', data)
        self.assertEqual(data['name'], "John Doe")
        self.assertEqual(data['phone_num'], "9876543212")
        self.assertEqual(data['status'], "active")
        
        # Verify Django User object is successfully created
        user_exists = User.objects.filter(username="john_doe").exists()
        self.assertTrue(user_exists)
        user = User.objects.get(username="john_doe")
        self.assertEqual(user.first_name, "John Doe")
        self.assertTrue(user.check_password('pass'))

        # Verify Driver record is successfully created in database
        driver_exists = Driver.objects.filter(user_name="John Doe").exists()
        self.assertTrue(driver_exists)
        driver = Driver.objects.get(user_name="John Doe")
        self.assertEqual(driver.phone_number, "9876543212")
        self.assertTrue(driver.license_number.startswith("LIC-"))

class StaffCreateAPITest(APITestCase):
    def setUp(self):
        # Create Location
        from staff.models import Location
        self.chennai = Location.objects.create(name="Chennai", short_code="CHN")

        # Create Users
        self.admin_user = User.objects.create_superuser(username="admin", password="adminpassword", is_staff=True)
        self.staff_user = User.objects.create_user(username="staff", password="staffpassword")
        
        self.url = reverse('create-staff-user')

    def test_anonymous_access_denied(self):
        payload = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'password': 'secretpassword',
            'assigned_location': self.chennai.id
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_access_denied(self):
        self.client.force_authenticate(user=self.staff_user)
        payload = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'password': 'secretpassword',
            'assigned_location': self.chennai.id
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access_allowed_and_creates_account_and_staff(self):
        self.client.force_authenticate(user=self.admin_user)
        
        payload = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'password': 'secretpassword',
            'assigned_location': self.chennai.id
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        data = response.json()
        
        # Verify response structure matches StaffListSerializer
        self.assertIn('staff_id', data)
        self.assertEqual(data['name'], "John Doe")
        self.assertEqual(data['email'], "john@example.com")
        self.assertEqual(data['assigned_location'], "Chennai")
        self.assertEqual(data['status'], "active")
        
        # Verify Django User object is successfully created
        user_exists = User.objects.filter(username="john_doe").exists()
        self.assertTrue(user_exists)
        user = User.objects.get(username="john_doe")
        self.assertEqual(user.first_name, "John Doe")
        self.assertEqual(user.email, "john@example.com")
        self.assertTrue(user.check_password('secretpassword'))

        # Verify StaffAccount record is successfully created in database
        staff_exists = StaffAccount.objects.filter(user=user).exists()
        self.assertTrue(staff_exists)
        staff = StaffAccount.objects.get(user=user)
        self.assertEqual(staff.assigned_location, self.chennai)

class VehicleListAPITest(APITestCase):
    def setUp(self):
        # Create Vehicles
        self.vehicle1 = Vehicle.objects.create(vehicle_number="TN-01-AB-1111")
        self.vehicle2 = Vehicle.objects.create(vehicle_number="TN-01-AB-2222")
        
        # Create Users
        self.admin_user = User.objects.create_superuser(username="admin", password="adminpassword", is_staff=True)
        self.staff_user = User.objects.create_user(username="staff", password="staffpassword")
        
        self.url = reverse('vehicle-list-admin')

    def test_anonymous_access_denied(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_access_denied(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access_allowed_and_correct_data(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        if isinstance(data, dict) and 'results' in data:
            results = data['results']
        else:
            results = data
            
        self.assertEqual(len(results), 2)
        
        first_item = results[0]
        self.assertEqual(first_item['id'], self.vehicle1.id)
        self.assertEqual(first_item['vehicle_number'], "TN-01-AB-1111")

        second_item = results[1]
        self.assertEqual(second_item['id'], self.vehicle2.id)
        self.assertEqual(second_item['vehicle_number'], "TN-01-AB-2222")

class VehicleCreateAPITest(APITestCase):
    def setUp(self):
        # Create Users
        self.admin_user = User.objects.create_superuser(username="admin", password="adminpassword", is_staff=True)
        self.staff_user = User.objects.create_user(username="staff", password="staffpassword")
        
        self.url = reverse('vehicle-create-admin')

    def test_anonymous_access_denied(self):
        payload = {
            'driver_name': 'Ram Kumar',
            'vehicle_name': 'TN-01-AB-9999'
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_access_denied(self):
        self.client.force_authenticate(user=self.staff_user)
        payload = {
            'driver_name': 'Ram Kumar',
            'vehicle_name': 'TN-01-AB-9999'
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access_allowed_and_creates_vehicle_and_driver(self):
        self.client.force_authenticate(user=self.admin_user)
        
        payload = {
            'driver_name': 'Ram Kumar',
            'vehicle_name': 'TN-01-AB-9999'
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        data = response.json()
        
        # Verify response structure matches VehicleListSerializer
        self.assertIn('id', data)
        self.assertEqual(data['vehicle_number'], "TN-01-AB-9999")
        
        # Verify Driver is created in the database
        driver_exists = Driver.objects.filter(user_name="Ram Kumar").exists()
        self.assertTrue(driver_exists)
        driver = Driver.objects.get(user_name="Ram Kumar")
        self.assertTrue(driver.license_number.startswith("LIC-"))

        # Verify Vehicle is created in the database
        vehicle_exists = Vehicle.objects.filter(vehicle_number="TN-01-AB-9999").exists()
        self.assertTrue(vehicle_exists)

class GDMDetailsListAPITest(APITestCase):
    def setUp(self):
        from staff.models import Location, Route, Driver, Courier, Payment, GDM, StaffAccount
        
        # Create Locations
        self.chennai = Location.objects.create(name="Chennai", short_code="CHN")
        self.bangalore = Location.objects.create(name="Bangalore", short_code="BLR")
        
        # Create Users
        self.admin_user = User.objects.create_superuser(username="admin", password="adminpassword", is_staff=True)
        self.staff_user = User.objects.create_user(username="staff", password="staffpassword")
        self.staff_account = StaffAccount.objects.create(user=self.staff_user, assigned_location=self.chennai)

        # Create Driver
        self.driver = Driver.objects.create(user_name="Rajesh Kumar", license_number="LIC-12345", phone_number="9876543210")

        # Create Route
        self.route = Route.objects.create(
            from_location=self.chennai,
            to_location=self.bangalore,
            route_path=["Chennai", "Vellore", "Bangalore"],
            driver=self.driver,
            vehicle=Vehicle.objects.create(vehicle_number="TN-01-AB-7777")
        )

        # Create Payments
        self.payment_paid = Payment.objects.create(amount=500, status="Paid", mode="Cash")
        self.payment_to_pay = Payment.objects.create(amount=600, status="To Pay", mode="None")

        # Create Couriers
        self.courier1 = Courier.objects.create(
            created_by=self.staff_account,
            from_location=self.chennai,
            to_location=self.bangalore,
            sender_name="Sender Chennai",
            receiver_name="Customer Chennai",
            from_address="Chennai Address",
            to_address="Bangalore Address",
            sender_phone_num="1234567890",
            receiver_phone_num="0987654321",
            parcel_information=[["Docs", 1]],
            route=self.route,
            payment=self.payment_paid,
            freight=500,
            weight=10,
            delivery_type="Door Delivery"
        )
        self.courier2 = Courier.objects.create(
            created_by=self.staff_account,
            from_location=self.chennai,
            to_location=self.bangalore,
            sender_name="Sender Bangalore",
            receiver_name="Customer Bangalore",
            from_address="Chennai Address",
            to_address="Bangalore Address",
            sender_phone_num="1234567890",
            receiver_phone_num="0987654321",
            parcel_information=[["Box", 1]],
            route=self.route,
            payment=self.payment_to_pay,
            freight=600,
            weight=15,
            delivery_type="Door Delivery"
        )


        # Create GDM
        self.gdm = GDM.objects.create(
            created_by=self.staff_account,
            vehicle_number="TN-01-AB-7777",
            driver=self.driver,
            route=self.route
        )
        self.gdm.couriers.add(self.courier1, self.courier2)
        
        self.url = reverse('gdm-details-admin')

    def test_anonymous_access_denied(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_access_denied(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access_allowed_and_correct_gdm_details(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        if isinstance(data, dict) and 'results' in data:
            results = data['results']
        else:
            results = data
            
        self.assertEqual(len(results), 1)
        gdm_details = results[0]
        
        self.assertEqual(gdm_details['gdm_number'], self.gdm.gdm_number)
        self.assertEqual(gdm_details['vehicle_number'], "TN-01-AB-7777")
        self.assertEqual(gdm_details['driver_name'], "Rajesh Kumar")
        self.assertEqual(gdm_details['total_freight'], 1100) # 500 + 600
        
        couriers = gdm_details['couriers']
        self.assertEqual(len(couriers), 2)
        
        c1 = [c for c in couriers if c['lr_num'] == self.courier1.lr_number][0]
        self.assertEqual(c1['customer_name'], "Customer Chennai")
        self.assertEqual(c1['status'], "paid")
        self.assertEqual(c1['freight'], 500)
        self.assertEqual(c1['route'], "Chennai -> Bangalore")

        c2 = [c for c in couriers if c['lr_num'] == self.courier2.lr_number][0]
        self.assertEqual(c2['customer_name'], "Customer Bangalore")
        self.assertEqual(c2['status'], "not paid")
        self.assertEqual(c2['freight'], 600)
        self.assertEqual(c2['route'], "Chennai -> Bangalore")








