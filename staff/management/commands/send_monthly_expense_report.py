from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.utils import timezone
from staff.models import Expense
from backend.config import ADMIN_EMAIL
import csv
import io

class Command(BaseCommand):
    help = 'Generate and send a monthly expense report via email as a CSV attachment'

    def handle(self, *args, **kwargs):
        # 1. Get the current year and month
        today = timezone.now().date()
        
        # Check if today is the last day of the month
        tomorrow = today + timezone.timedelta(days=1)
        if tomorrow.month == today.month:
            self.stdout.write(self.style.NOTICE("Today is not the last day of the month. Skipping report generation."))
            return
            
        # 2. Query expenses for the current month
        expenses = Expense.objects.filter(
            created_at__year=today.year,
            created_at__month=today.month
        ).order_by('created_at')

        if not expenses.exists():
            self.stdout.write(self.style.WARNING(f"No expenses found for {today.strftime('%B %Y')}."))
            return

        # 3. Create a CSV file in memory
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        
        # Write the header
        writer.writerow(['ID', 'Reason', 'Staff Username', 'Staff ID', 'Text', 'Amount', 'Date'])
        
        # Write the data
        total_amount = 0
        for expense in expenses:
            writer.writerow([
                expense.id,
                expense.reason.name if expense.reason else 'N/A',
                expense.staff.user.username if expense.staff and expense.staff.user else 'N/A',
                expense.staff.staffID if expense.staff else 'N/A',
                expense.text or '',
                expense.amount,
                expense.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
            total_amount += expense.amount
        
        # Write the total at the bottom
        writer.writerow([])
        writer.writerow(['', '', '', '', 'Total Amount:', total_amount, ''])

        # 4. Prepare the email
        subject = f"Monthly Expense Report - {today.strftime('%B %Y')}"
        body = (
            f"Hello Admin,\n\n"
            f"Please find attached the detailed expense report for {today.strftime('%B %Y')}.\n\n"
            f"Total Expenses: {total_amount}\n\n"
            f"Best regards,\nCourier Agency System"
        )
        
        email = EmailMessage(
            subject=subject,
            body=body,
            to=[ADMIN_EMAIL],
        )
        
        # Attach the CSV
        csv_filename = f"expense_report_{today.strftime('%Y_%m')}.csv"
        email.attach(csv_filename, csv_buffer.getvalue(), 'text/csv')
        
        # 5. Send the email
        try:
            email.send()
            self.stdout.write(self.style.SUCCESS(f"Successfully sent the monthly expense report to {ADMIN_EMAIL}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email: {e}"))
