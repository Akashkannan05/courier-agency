from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors

def generate_courier_pdf(courier):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(1 * inch, height - 1 * inch, "Courier Agency - Booking Receipt")
    
    p.setFont("Helvetica", 10)
    p.drawString(1 * inch, height - 1.25 * inch, f"Invoice Number: {courier.invoice_number}")
    p.drawString(1 * inch, height - 1.4 * inch, f"Date: {courier.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    p.drawString(1 * inch, height - 1.55 * inch, f"Booked By: {courier.created_by.user.get_full_name() or courier.created_by.user.username}")

    # Locations
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1 * inch, height - 2 * inch, "Route Information")
    p.setFont("Helvetica", 10)
    p.drawString(1.2 * inch, height - 2.2 * inch, f"From: {courier.from_location.name}")
    p.drawString(1.2 * inch, height - 2.35 * inch, f"To: {courier.to_location.name}")
    p.drawString(1.2 * inch, height - 2.5 * inch, f"Delivery Type: {courier.delivery_type}")
    if courier.vehicle:
        p.drawString(1.2 * inch, height - 2.65 * inch, f"Vehicle: {courier.vehicle.vehicle_number} ({courier.vehicle.driver_name})")

    # Sender & Receiver
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1 * inch, height - 3 * inch, "Sender Details")
    p.setFont("Helvetica", 10)
    p.drawString(1.2 * inch, height - 3.2 * inch, f"Name: {courier.sender_name}")
    p.drawString(1.2 * inch, height - 3.35 * inch, f"Address: {courier.from_address}")
    p.drawString(1.2 * inch, height - 3.5 * inch, f"Phone: {courier.sender_phone_num}")

    p.setFont("Helvetica-Bold", 12)
    p.drawString(4 * inch, height - 3 * inch, "Receiver Details")
    p.setFont("Helvetica", 10)
    p.drawString(4.2 * inch, height - 3.2 * inch, f"Name: {courier.receiver_name}")
    p.drawString(4.2 * inch, height - 3.35 * inch, f"Address: {courier.to_address}")
    p.drawString(4.2 * inch, height - 3.5 * inch, f"Phone: {courier.receiver_phone_num}")

    # Parcel Info
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1 * inch, height - 4 * inch, "Parcel Information")
    p.setFont("Helvetica", 10)
    y = height - 4.2 * inch
    p.drawString(1.2 * inch, y, f"Weight: {courier.weight} kg")
    y -= 0.15 * inch
    p.drawString(1.2 * inch, y, "Contents:")
    for item in courier.parcel_information:
        y -= 0.15 * inch
        p.drawString(1.4 * inch, y, f"- {item[0]}: {item[1]} packages")

    # Financials
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1 * inch, height - 5.5 * inch, "Payment Details")
    p.setFont("Helvetica", 10)
    y = height - 5.7 * inch
    charges = [
        ("Freight", courier.freight),
        ("Loading/Unloading", courier.loading_unloading),
        ("Door Pickup", courier.door_pickup),
        ("Other Transport", courier.other_transport_crossing),
        ("Mamool", courier.mamool),
        ("Statistical Charges", courier.statistical_charges),
        ("Door Delivery", courier.door_delivery),
    ]
    for label, amount in charges:
        if amount > 0:
            p.drawString(1.2 * inch, y, f"{label}: {amount}")
            y -= 0.15 * inch

    p.line(1 * inch, y, 3 * inch, y)
    y -= 0.2 * inch
    p.setFont("Helvetica-Bold", 11)
    p.drawString(1.2 * inch, y, f"Total Amount: {courier.total}")
    
    y -= 0.2 * inch
    p.setFont("Helvetica", 10)
    p.drawString(1.2 * inch, y, f"Payment Status: {courier.payment.status}")
    p.drawString(1.2 * inch, y - 0.15 * inch, f"Payment Mode: {courier.payment.mode}")

    # Footer
    p.setFont("Helvetica-Oblique", 8)
    p.drawCentredString(width / 2.0, 0.5 * inch, "Thank you for using our Courier Service!")

    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer
