from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.utils import timezone
from staff.models import GDM
from backend.config import ADMIN_EMAIL
import csv
import io
from collections import defaultdict

class Command(BaseCommand):
    help = 'Generate and send a monthly GDM report via email as a CSV attachment grouped by date'

    def handle(self, *args, **kwargs):
        # 1. Get the current year and month
        today = timezone.now().date()
        
        # Check if today is the last day of the month
        tomorrow = today + timezone.timedelta(days=1)
        if tomorrow.month == today.month:
            self.stdout.write(self.style.NOTICE("Today is not the last day of the month. Skipping report generation."))
            return
            
        # 2. Query GDMs for the current month
        gdms = GDM.objects.filter(
            dispatch_date__year=today.year,
            dispatch_date__month=today.month
        ).order_by('dispatch_date')

        if not gdms.exists():
            self.stdout.write(self.style.WARNING(f"No GDMs found for {today.strftime('%B %Y')}."))
            return

        # 3. Group by date
        gdms_by_date = defaultdict(list)
        for gdm in gdms:
            gdm_date = gdm.dispatch_date.date()
            gdms_by_date[gdm_date].append(gdm)

        # 4. Create a CSV file in memory
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        
        total_couriers_month = 0
        total_weight_month = 0
        total_price_month = 0

        # Write the data grouped by date
        for gdm_date in sorted(gdms_by_date.keys()):
            # Write a row for the Date
            writer.writerow([f"Date: {gdm_date.strftime('%Y-%m-%d')}"])
            writer.writerow([
                'GDM Number', 'Vehicle Number', 'Driver Name', 
                'Driver Phone', 'Route (From - To)', 'Dispatch Time', 
                'Total Couriers', 'Total Weights', 'Total Price'
            ])
            
            date_couriers = 0
            date_weight = 0
            date_price = 0

            for gdm in gdms_by_date[gdm_date]:
                writer.writerow([
                    gdm.gdm_number or 'N/A',
                    gdm.vehicle_number,
                    gdm.driver_name,
                    gdm.driver_phone_num or 'N/A',
                    f"{gdm.route.from_location.name} - {gdm.route.to_location.name}",
                    gdm.dispatch_date.strftime('%H:%M:%S'),
                    gdm.total_couriers_count,
                    gdm.total_weights,
                    gdm.total_price
                ])
                date_couriers += gdm.total_couriers_count
                date_weight += gdm.total_weights
                date_price += gdm.total_price
            
            # Write totals for the date
            writer.writerow(['', '', '', '', '', 'Daily Total:', date_couriers, date_weight, date_price])
            writer.writerow([]) # Empty row for separation
            
            total_couriers_month += date_couriers
            total_weight_month += date_weight
            total_price_month += date_price

        # Write the overall total at the bottom
        writer.writerow(['', '', '', '', '', 'Monthly Total:', total_couriers_month, total_weight_month, total_price_month])

        # 5. Prepare the email
        subject = f"Monthly GDM Report - {today.strftime('%B %Y')}"
        body = (
            f"Hello Admin,\n\n"
            f"Please find attached the detailed GDM report for {today.strftime('%B %Y')}.\n\n"
            f"Total GDMs Dispatched: {gdms.count()}\n"
            f"Total Couriers Shipped: {total_couriers_month}\n"
            f"Total Weight Shipped: {total_weight_month}\n"
            f"Total Price: {total_price_month}\n\n"
            f"Best regards,\nCourier Agency System"
        )
        
        email = EmailMessage(
            subject=subject,
            body=body,
            to=[ADMIN_EMAIL],
        )
        
        # Attach the CSV
        csv_filename = f"gdm_report_{today.strftime('%Y_%m')}.csv"
        email.attach(csv_filename, csv_buffer.getvalue(), 'text/csv')
        
        # 6. Send the email
        try:
            email.send()
            self.stdout.write(self.style.SUCCESS(f"Successfully sent the monthly GDM report to {ADMIN_EMAIL}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email: {e}"))
