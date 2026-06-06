from django.conf import settings
from twilio.rest import Client
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors

# def generate_courier_pdf(courier):
#     buffer = BytesIO()
#     p = canvas.Canvas(buffer, pagesize=letter)
#     width, height = letter

#     # Header
#     p.setFont("Helvetica-Bold", 16)
#     p.drawString(1 * inch, height - 1 * inch, "Courier Agency - Booking Receipt")
    
#     p.setFont("Helvetica", 10)
#     p.drawString(1 * inch, height - 1.25 * inch, f"Invoice Number: {courier.invoice_number}")
#     p.drawString(1 * inch, height - 1.4 * inch, f"Date: {courier.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
#     p.drawString(1 * inch, height - 1.55 * inch, f"Booked By: {courier.created_by.user.get_full_name() or courier.created_by.user.username}")

#     # Locations
#     p.setFont("Helvetica-Bold", 12)
#     p.drawString(1 * inch, height - 2 * inch, "Route Information")
#     p.setFont("Helvetica", 10)
#     p.drawString(1.2 * inch, height - 2.2 * inch, f"From: {courier.from_location.name}")
#     p.drawString(1.2 * inch, height - 2.35 * inch, f"To: {courier.to_location.name}")
#     p.drawString(1.2 * inch, height - 2.5 * inch, f"Delivery Type: {courier.delivery_type}")
#     if courier.vehicle:
#         p.drawString(1.2 * inch, height - 2.65 * inch, f"Vehicle: {courier.vehicle.vehicle_number} ({courier.vehicle.driver_name})")

#     # Sender & Receiver
#     p.setFont("Helvetica-Bold", 12)
#     p.drawString(1 * inch, height - 3 * inch, "Sender Details")
#     p.setFont("Helvetica", 10)
#     p.drawString(1.2 * inch, height - 3.2 * inch, f"Name: {courier.sender_name}")
#     p.drawString(1.2 * inch, height - 3.35 * inch, f"Address: {courier.from_address}")
#     p.drawString(1.2 * inch, height - 3.5 * inch, f"Phone: {courier.sender_phone_num}")

#     p.setFont("Helvetica-Bold", 12)
#     p.drawString(4 * inch, height - 3 * inch, "Receiver Details")
#     p.setFont("Helvetica", 10)
#     p.drawString(4.2 * inch, height - 3.2 * inch, f"Name: {courier.receiver_name}")
#     p.drawString(4.2 * inch, height - 3.35 * inch, f"Address: {courier.to_address}")
#     p.drawString(4.2 * inch, height - 3.5 * inch, f"Phone: {courier.receiver_phone_num}")

#     # Parcel Info
#     p.setFont("Helvetica-Bold", 12)
#     p.drawString(1 * inch, height - 4 * inch, "Parcel Information")
#     p.setFont("Helvetica", 10)
#     y = height - 4.2 * inch
#     p.drawString(1.2 * inch, y, f"Weight: {courier.weight} kg")
#     y -= 0.15 * inch
#     p.drawString(1.2 * inch, y, "Contents:")
#     for item in courier.parcel_information:
#         y -= 0.15 * inch
#         p.drawString(1.4 * inch, y, f"- {item[0]}: {item[1]} packages")

#     # Financials
#     p.setFont("Helvetica-Bold", 12)
#     p.drawString(1 * inch, height - 5.5 * inch, "Payment Details")
#     p.setFont("Helvetica", 10)
#     y = height - 5.7 * inch
#     charges = [
#         ("Freight", courier.freight),
#         ("Loading/Unloading", courier.loading_unloading),
#         ("Door Pickup", courier.door_pickup),
#         ("Other Transport", courier.other_transport_crossing),
#         ("Mamool", courier.mamool),
#         ("Statistical Charges", courier.statistical_charges),
#         ("Door Delivery", courier.door_delivery),
#     ]
#     for label, amount in charges:
#         if amount > 0:
#             p.drawString(1.2 * inch, y, f"{label}: {amount}")
#             y -= 0.15 * inch

#     p.line(1 * inch, y, 3 * inch, y)
#     y -= 0.2 * inch
#     p.setFont("Helvetica-Bold", 11)
#     p.drawString(1.2 * inch, y, f"Total Amount: {courier.total}")
    
#     y -= 0.2 * inch
#     p.setFont("Helvetica", 10)
#     p.drawString(1.2 * inch, y, f"Payment Status: {courier.payment.status}")
#     p.drawString(1.2 * inch, y - 0.15 * inch, f"Payment Mode: {courier.payment.mode}")

#     # Footer
#     p.setFont("Helvetica-Oblique", 8)
#     p.drawCentredString(width / 2.0, 0.5 * inch, "Thank you for using our Courier Service!")

#     p.showPage()
#     p.save()
    
#     buffer.seek(0)
#     return buffer

"""
S A Salem Super Service – Lorry Way Bill
Half-A4 (210 × 148.5 mm)  ·  ReportLab canvas

Space budget (142.5 mm usable after 3mm margins each side):
  Header title row      :  10.0 mm
  Office / contact grid :  22.0 mm  (hard cap)
  LORRY WAY BILL bar    :   5.5 mm
  ── body rows ──
  FROM / TO             :   7.0 mm
  Consignor / Consignee :   7.0 mm
  Address               :   7.5 mm  (auto-grows if text wraps)
  Phone                 :   6.0 mm
  Pkg / Wt / Delivery   :   5.5 mm
  Contents              :   5.5 mm
  ── charges + info ──
  7 charge rows         :  30.1 mm  (7 × 4.3 mm)
  TOTAL row             :   5.5 mm
  ── footer ──
  Bank + signature      :  11.0 mm
  ────────────────────────────────
  Nominal total         : 122.6 mm  (19.9 mm breathing room)

Key design decisions
--------------------
1. Office text font reduced to 4.8 pt with 3.1 mm line-height → fits 6 lines in 22 mm.
2. Cell label/value sizes kept at 5 pt / 6.5 pt (was 5/7) → saves ~1 mm per row.
3. Charge rows reduced to 4.3 mm height.
4. Signature box merged INTO the footer row (right third) – no separate strip.
5. Info row (Invoice/Date/Payment/BookedBy) height = charge table height exactly.
6. draw_table_row() enforces a MIN_ROW_H floor so short values don't shrink too much.
7. All coordinate origins are derived from the y-cursor; nothing hardcoded.
"""

from io import BytesIO
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib import colors

# ── Page ──────────────────────────────────────────────────────────────────────
PW = 210 * mm
PH = 148.5 * mm

# ── Palette ───────────────────────────────────────────────────────────────────
C_BLUE  = colors.HexColor("#1A237E")
C_WHITE = colors.white
C_BLACK = colors.black

# ── Fonts ─────────────────────────────────────────────────────────────────────
FB = "Helvetica-Bold"
FR = "Helvetica"

# ── Typography scale (all reduced from previous version) ─────────────────────
SZ_TITLE   = 13      # company name
SZ_SUB     =  6.5   # "REGULAR PARCEL SERVICE"
SZ_INV     =  6.5   # invoice number (top-right)
SZ_OFF_H   =  5.2   # office heading
SZ_OFF_B   =  4.8   # office body text
SZ_LBL     =  4.8   # cell label (small text above value)
SZ_VAL     =  7.5   # cell value normal
SZ_VALSM   =  6.0   # cell value small (address)
SZ_CHG     =  5.8   # charge row text
SZ_FOOT    =  5.3   # footer bank text

# ── Spacing constants ─────────────────────────────────────────────────────────
HP         = 1.3 * mm   # horizontal inner padding
VP         = 2 * mm   # vertical inner padding
LBL_STRIP  = 5.9 * mm   # height of the label area inside a cell
LH_VAL     = 1 * mm   # value line-height inside cells
LH_OFF     = 3 * mm   # office address line-height
LH_CHG     = 4 * mm   # charge row height
MIN_ROW_H  = 7.0 * mm   # floor for body rows
ADDR_H_MAX = 22.0 * mm  # hard cap on office-grid height
FOOTER_H   = 11.0 * mm  # bank details + signature + bottom border


# ═══════════════════════════════════════════════════════════════════════════════
class Renderer:
    """
    Wraps ReportLab canvas.  All drawing goes through methods here so that
    coordinate arithmetic stays in one place and primitives are reusable.
    y convention: y = TOP of the element (we subtract height to get bottom).
    """

    def __init__(self, buf):
        self.c   = rl_canvas.Canvas(buf, pagesize=(PW, PH))
        self.PAD = 3 * mm
        self.BL  = self.PAD + 1 * mm
        self.BR  = PW - self.PAD - 1 * mm
        self.BW  = self.BR - self.BL
        # Safe bottom boundary – footer must not cross this
        self.SAFE_BOT = self.PAD + FOOTER_H

    # ── Primitives ────────────────────────────────────────────────────────────

    def hline(self, x1, x2, y, lw=0.4):
        self.c.setStrokeColor(C_BLUE)
        self.c.setLineWidth(lw)
        self.c.line(x1, y, x2, y)

    def vline(self, x, y1, y2, lw=0.4):
        self.c.setStrokeColor(C_BLUE)
        self.c.setLineWidth(lw)
        self.c.line(x, y1, x, y2)

    def box(self, x, y_top, w, h, lw=0.4, fill=None):
        """Draw rectangle. y_top = top edge."""
        self.c.setStrokeColor(C_BLUE)
        self.c.setLineWidth(lw)
        if fill:
            self.c.setFillColor(fill)
            self.c.rect(x, y_top - h, w, h, stroke=1, fill=1)
        else:
            self.c.rect(x, y_top - h, w, h, stroke=1, fill=0)

    def txt(self, x, y, s, font=FR, size=7, color=C_BLACK, align="left"):
        """Draw text. y = baseline."""
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        s = str(s)
        if   align == "center": self.c.drawCentredString(x, y, s)
        elif align == "right":  self.c.drawRightString(x, y, s)
        else:                   self.c.drawString(x, y, s)

    def sw(self, s, font, size):
        return self.c.stringWidth(str(s), font, size)

    # ── Text wrapping ─────────────────────────────────────────────────────────

    def wrap(self, text, font, size, max_w):
        """Return list of word-wrapped lines that fit within max_w."""
        words = str(text).split()
        if not words:
            return [""]
        lines, cur = [], words[0]
        for w in words[1:]:
            test = cur + " " + w
            if self.sw(test, font, size) <= max_w:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        return lines

    def draw_wrapped(self, x, y_top, text, font, size, max_w, lh,
                     color=C_BLACK):
        """Draw wrapped text. y_top = baseline of first line. Returns y after last."""
        for ln in self.wrap(text, font, size, max_w):
            self.txt(x, y_top, ln, font=font, size=size, color=color)
            y_top -= lh
        return y_top

    # ── Cell ──────────────────────────────────────────────────────────────────

    def cell_height(self, value, w, val_sz=SZ_VAL):
        """Minimum height a cell needs for this value."""
        inner = w - 2 * HP
        n = len(self.wrap(value, FB, val_sz, inner))
        return LBL_STRIP + n * LH_VAL + VP

    def draw_cell(self, x, y_top, w, h, label, value,
                  lbl_sz=SZ_LBL, val_sz=SZ_VAL):
        """
        Draw a bordered cell (label at top, wrapped bold value below).
        x, y_top = top-left corner.  h = allocated height.
        """
        self.box(x, y_top, w, h)
        inner_w = w - 2 * HP
        # label baseline: just inside top edge
        self.txt(x + HP, y_top - VP - lbl_sz * 0.7,
                 label, size=lbl_sz, color=C_BLUE)
        # value: starts just below label strip
        self.draw_wrapped(x + HP, y_top - LBL_STRIP,
                          value, FB, val_sz, inner_w, LH_VAL)

    # ── Table row ─────────────────────────────────────────────────────────────

    def draw_table_row(self, x_start, y_top, col_widths, cells):
        """
        Render N cells side-by-side.
        cells: list of (label, value) or (label, value, val_sz).
        All cells share the tallest computed height (floor = MIN_ROW_H).
        Returns height consumed.
        """
        row_h = MIN_ROW_H
        for i, cell in enumerate(cells):
            val_sz = cell[2] if len(cell) > 2 else SZ_VAL
            row_h  = max(row_h, self.cell_height(cell[1], col_widths[i], val_sz))

        x = x_start
        for i, cell in enumerate(cells):
            val_sz = cell[2] if len(cell) > 2 else SZ_VAL
            self.draw_cell(x, y_top, col_widths[i], row_h,
                           cell[0], cell[1], val_sz=val_sz)
            x += col_widths[i]
        return row_h

    # ── Checkbox ──────────────────────────────────────────────────────────────

    def draw_checkbox(self, x, y_mid, label, checked):
        """Uniform 2.8 mm checkbox + label. y_mid = vertical centre of box."""
        SZ = 2.8 * mm
        by = y_mid - SZ / 2
        self.box(x, by + SZ, SZ, SZ)          # box(x, y_top, w, h)
        if checked:
            pad = SZ * 0.2
            self.box(x + pad, by + SZ - pad, SZ - 2*pad, SZ - 2*pad,
                     fill=C_BLUE)
        self.txt(x + SZ + 1.0*mm, by + SZ*0.15,
                 label, size=SZ_CHG)

    def save(self):
        self.c.showPage()
        self.c.save()


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION: HEADER
# ═══════════════════════════════════════════════════════════════════════════════

def draw_header(r: Renderer, invoice_num: str) -> float:
    """
    Draws:
      • White background + outer border
      • Title row (MCC | Company name | No.)
      • Office grid  col-8  + Contact box  col-4
    Returns y at the bottom of the header separator line.
    """
    BL, BR, BW = r.BL, r.BR, r.BW
    top = PH - r.PAD   # inner top

    # ── Background + border ───────────────────────────────────────────────────
    # Fill white first, then stroke border on top
    r.c.setFillColor(C_WHITE)
    r.c.rect(0, 0, PW, PH, stroke=0, fill=1)
    r.box(r.PAD, PH - r.PAD, PW - 2*r.PAD, PH - 2*r.PAD, lw=1.2)

    # ── Title row (10 mm tall) ────────────────────────────────────────────────
    TITLE_H = 10.0 * mm
    r.txt(BL,   top - 5.0*mm, "MCC",
          font=FB, size=9, color=C_BLUE)
    r.txt(PW/2, top - 4.5*mm, "S A Salem Super Service",
          font=FB, size=SZ_TITLE, color=C_BLUE, align="center")
    r.txt(PW/2, top - 8.5*mm, "REGULAR PARCEL SERVICE",
          font=FB, size=SZ_SUB,   color=C_BLUE, align="center")
    r.txt(BR,   top - 4.5*mm, f"No. : {invoice_num}",
          font=FB, size=SZ_INV, align="right")
    r.hline(BL, BR, top - TITLE_H, lw=0.8)

    # ── Office / contact section ──────────────────────────────────────────────
    # col-8 = 4 equal office columns,  col-4 = contact+email box
    ADDR_W    = BW * 8 / 12
    CONTACT_W = BW * 4 / 12
    col_w     = ADDR_W / 4
    # Safe inner text width for each office column (leave 0.5 mm gap from divider)
    inner_w   = col_w - 2 * HP - 0.5 * mm

    offices = [
        ("COIMBATORE OFF:", [
            "5/3, Nadar Street,",
            "Nayakkar Thottam,",
            "Coimbatore-641001",
            "MOB:98527 07051,",
            "93610 04578",
        ]),
        ("SALEM OFF:", [
            "196/2, Ambalavan Swamy",
            "Koil St, Santhaipettai",
            "Main Rd, Shevapettai,",
            "Salem-636002",
            "Ph:0427 4961944",
            "MOB:93845 10141",
        ]),
        ("CHENNAI OFFICE:", [
            "2/29, Perumal Koil",
            "Garden St, First Ln,",
            "(Off Walltax Rd),",
            "Chennai-600079",
            "Ph:044-42144944",
            "MOB:63811 90433",
        ]),
        ("VELLORE OFFICE:", [
            "8, Old Bangalore Rd,",
            "Opp Govt School,",
            "Konavattam,",
            "Vellore-632008",
            "MOB:89254 43953",
        ]),
    ]

    # Uniform height = tallest column, capped at ADDR_H_MAX
    max_lines = max(len(lines) for _, lines in offices)
    # heading line + body lines + top/bottom padding
    addr_box_h = min(
        (1 + max_lines) * LH_OFF + 2 * VP,
        ADDR_H_MAX,
    )
    addr_box_h = max(addr_box_h, 18 * mm)

    addr_top = top - TITLE_H   # top of address box (flush to separator)
    addr_bot = addr_top - addr_box_h

    for i, (heading, lines) in enumerate(offices):
        cx = BL + i * col_w
        tx = cx + HP
        ty = addr_top - VP

        # Vertical divider between columns (skip leftmost)
        if i > 0:
            r.vline(cx, addr_top, addr_bot, lw=0.3)

        # Heading – hard-clip to inner_w
        h_txt = heading
        while r.sw(h_txt, FB, SZ_OFF_H) > inner_w and len(h_txt) > 4:
            h_txt = h_txt[:-1]
        r.txt(tx, ty, h_txt, font=FB, size=SZ_OFF_H)
        ty -= LH_OFF

        # Body lines – clip each line to fit
        for ln in lines:
            if ty < addr_bot + VP:   # don't render below box bottom
                break
            b = ln
            while r.sw(b, FR, SZ_OFF_B) > inner_w and len(b) > 3:
                b = b[:-1]
            r.txt(tx, ty, b, font=FR, size=SZ_OFF_B)
            ty -= LH_OFF

    # Border around the 4-column address block
    r.box(BL, addr_top, ADDR_W, addr_box_h, lw=0.6)

    # ── Contact box (right col-4) ─────────────────────────────────────────────
    cx0   = BL + ADDR_W
    mid_y = addr_top - addr_box_h / 2

    r.box(cx0, addr_top, CONTACT_W, addr_box_h, lw=0.6)
    r.txt(cx0 + CONTACT_W/2, mid_y + 4.0*mm,
          "For All Bookings Contact:",
          font=FB, size=5.8, color=C_BLUE, align="center")
    r.txt(cx0 + CONTACT_W/2, mid_y + 0.5*mm,
          "98947 64712, 80156 14944",
          font=FB, size=6.2, color=C_BLUE, align="center")
    r.txt(cx0 + CONTACT_W/2, mid_y - 3.5*mm,
          "madrascc@gmail.com",
          font=FR, size=5.3, align="center")

    # Final separator line before way-bill bar
    sep_y = addr_bot - 0.5 * mm
    r.hline(BL, BR, sep_y, lw=0.8)
    return sep_y


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION: LORRY WAY BILL BAR
# ═══════════════════════════════════════════════════════════════════════════════

def draw_waybill_bar(r: Renderer, y: float) -> float:
    """Full-width dark-blue title bar. Returns y at bottom."""
    BAR_H = 5.5 * mm
    r.box(r.BL, y, r.BW, BAR_H, fill=C_BLUE, lw=0)
    r.txt(PW/2, y - BAR_H + 1.8*mm,
          "LORRY WAY BILL",
          font=FB, size=8.5, color=C_WHITE, align="center")
    return y - BAR_H


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION: BODY
# ═══════════════════════════════════════════════════════════════════════════════

def draw_body(r: Renderer, y: float, d: dict) -> float:
    """
    Draws all waybill data rows.
    Respects r.SAFE_BOT – stops rendering if we would overflow into footer.
    Returns y at the bottom of the last drawn element.
    """
    BL, BW = r.BL, r.BW
    half  = BW / 2
    third = BW / 3

    # Charge column widths (right side)
    CHG_LBL = 32 * mm
    CHG_CUR =  7 * mm
    CHG_AMT = 11 * mm
    CHG_W   = CHG_LBL + CHG_CUR + CHG_AMT
    LEFT_W  = BW - CHG_W   # width for invoice/date/payment/booked cols

    # ── Party rows (FROM/TO → Contents) ──────────────────────────────────────
    party_rows = [
        ([half, half],
         [("FROM", d.get("from_location","")),
          ("TO",   d.get("to_location",""))]),
        ([half, half],
         [("CONSIGNOR (Sender)",   d.get("sender_name","")),
          ("CONSIGNEE (Receiver)", d.get("receiver_name",""))]),
        ([half, half],
         [("Address", d.get("from_address",""), SZ_VALSM),
          ("Address", d.get("to_address",""),   SZ_VALSM)]),
        ([half, half],
         [("Phone", d.get("sender_phone_num","")),
          ("Phone", d.get("receiver_phone_num",""))]),
        ([third, third, third],
         [("No. of Packages", d.get("no_of_packages","")),
          ("Weight (kg)",     d.get("weight","")),
          ("Delivery Type",   d.get("delivery_type",""))]),
    ]
    # Contents row (full width)
    contents = ", ".join(f"{i[0]} ({i[1]} pkgs)"
                         for i in d.get("parcel_information", []))
    party_rows.append(([BW], [("Contents / Nature of Goods", contents, SZ_VALSM)]))

    for col_widths, cells in party_rows:
        rh = r.draw_table_row(BL, y, col_widths, cells)
        y -= rh

    # ── Charge table (right side) + Info row (left side) ─────────────────────
    charges = [
        ("Freight",                  d.get("freight", 0)),
        ("Loading & Unloading",      d.get("loading_unloading", 0)),
        ("Door Pickup",              d.get("door_pickup", 0)),
        ("D/D Charges",              d.get("dd_charges", 0)),
        ("Other Transport/Crossing", d.get("other_transport_crossing", 0)),
        ("Mamool",                   d.get("mamool", 0)),
        ("Statistical Charges",      d.get("statistical_charges", 0)),
    ]
    TOT_H = 5.5 * mm
    # Total height of the charge block (rows + TOTAL row)
    CHG_BLOCK_H = len(charges) * LH_CHG + TOT_H

    cx_lbl = BL + LEFT_W          # x: charge label column
    cx_cur = cx_lbl + CHG_LBL     # x: currency column
    cx_amt = cx_cur + CHG_CUR     # x: amount column

    cy = y  # cursor for charges (moves down)
    for label, amount in charges:
        r.box(cx_lbl, cy, CHG_LBL, LH_CHG, lw=0.4)
        r.box(cx_cur, cy, CHG_CUR, LH_CHG, lw=0.4)
        r.box(cx_amt, cy, CHG_AMT, LH_CHG, lw=0.4)
        # Vertically centre text in the charge row
        ty = cy - LH_CHG + (LH_CHG - SZ_CHG*0.352) / 2
        r.txt(cx_lbl + HP, ty, label, size=SZ_CHG)
        r.txt(cx_cur + HP, ty, "Rs.", size=SZ_CHG)
        amt_s = str(amount) if amount is not None else ""
        r.txt(cx_amt + CHG_AMT - HP, ty, amt_s,
              size=SZ_CHG, align="right")
        cy -= LH_CHG

    # TOTAL row
    r.box(cx_lbl, cy, CHG_W, TOT_H, fill=C_BLUE, lw=0.5)
    tot_ty = cy - TOT_H + (TOT_H - 7*0.352)/2
    r.txt(cx_lbl + HP, tot_ty, "TOTAL",
          font=FB, size=7, color=C_WHITE)
    r.txt(cx_cur + HP, tot_ty, "Rs.",
          font=FB, size=7, color=C_WHITE)
    r.txt(cx_amt + CHG_AMT - HP, tot_ty, str(d.get("total", 0)),
          font=FB, size=7, color=C_WHITE, align="right")

    charge_bottom = cy - TOT_H   # y at bottom of charge block

    # ── Info column (left side, 3 stacked rows matching charge block height) ───
    # Layout (top → bottom):
    #   Row A  : Invoice No.    (label + value)
    #   Row B  : Date           (label + value)
    #   Row C  : Payment Mode   (label + 3 inline checkboxes)
    # Total height = CHG_BLOCK_H so the right border of the charge table aligns.

    INFO_H = CHG_BLOCK_H

    # Divide INFO_H into 3 equal rows
    ROW_A_H = INFO_H / 3
    ROW_B_H = INFO_H / 3
    ROW_C_H = INFO_H - ROW_A_H - ROW_B_H   # absorbs any rounding remainder

    iy_a = y                    # top of Row A
    iy_b = iy_a - ROW_A_H      # top of Row B
    iy_c = iy_b - ROW_B_H      # top of Row C

    # ── Row A: Invoice No. ────────────────────────────────────────────────────
    r.box(BL, iy_a, LEFT_W, ROW_A_H, lw=0.4)
    r.txt(BL + HP, iy_a - VP - SZ_LBL * 0.7,
          "Invoice No.", size=SZ_LBL, color=C_BLUE)
    r.txt(BL + HP, iy_a - ROW_A_H + VP + SZ_VAL * 0.35,
          d.get("invoice_number", ""), font=FB, size=SZ_VAL)

    # ── Row B: Date ───────────────────────────────────────────────────────────
    r.box(BL, iy_b, LEFT_W, ROW_B_H, lw=0.4)
    r.txt(BL + HP, iy_b - VP - SZ_LBL * 0.7,
          "Date", size=SZ_LBL, color=C_BLUE)
    r.txt(BL + HP, iy_b - ROW_B_H + VP + SZ_VAL * 0.35,
          d.get("date", ""), font=FB, size=SZ_VAL)

    # ── Row C: Payment Mode (label + 3 inline checkboxes) ────────────────────
    paid   = d.get("payment_status", "").upper() == "PAID"
    to_pay = d.get("payment_status", "").upper() == "TO PAY"
    rtn    = d.get("payment_status", "").upper() == "RTN"

    r.box(BL, iy_c, LEFT_W, ROW_C_H, lw=0.4)
    r.txt(BL + HP, iy_c - VP - SZ_LBL * 0.7,
          "Payment Mode:", size=SZ_LBL, color=C_BLUE)

    # 3 checkboxes laid out horizontally, evenly spaced across LEFT_W
    CB_SZ    = 2.8 * mm
    MODES    = [("PAID", paid), ("TO PAY", to_pay), ("RTN", rtn)]
    # Estimate each checkbox+label slot width
    slot_w   = LEFT_W / len(MODES)
    cb_mid_y = iy_c - ROW_C_H / 2 - LBL_STRIP / 4   # vertical centre of checkbox row

    for mi, (lbl, chk) in enumerate(MODES):
        slot_x = BL + mi * slot_w
        # Centre checkbox within its slot
        lbl_w  = r.sw(lbl, "Helvetica", SZ_CHG)
        total_w = CB_SZ + 1.0*mm + lbl_w
        cb_x   = slot_x + (slot_w - total_w) / 2
        r.draw_checkbox(cb_x, cb_mid_y, lbl, chk)

    info_bottom = iy_c - ROW_C_H
    # Both sides end at the same y (by design: INFO_H == CHG_BLOCK_H)
    return min(charge_bottom, info_bottom)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION: FOOTER  (bank details left + signature right, single row)
# ═══════════════════════════════════════════════════════════════════════════════

def draw_footer(r: Renderer, y: float):
    """
    Single-row footer: left 60% = bank details, right 40% = signature box.
    y = top of footer band.
    """
    BL, BR, BW = r.BL, r.BR, r.BW
    r.hline(BL, BR, y, lw=0.8)

    BANK_W = BW * 0.60
    SIG_W  = BW * 0.40
    FH     = FOOTER_H - 1 * mm   # inner height (leave 1 mm for bottom border)

    # Bank text (two sub-columns inside BANK_W)
    col_a = BL
    col_b = BL + BANK_W * 0.50
    fy    = y - VP - SZ_FOOT * 0.7   # first line baseline

    r.txt(col_a, fy,           "Name : S A Salem Super Service", font=FB, size=SZ_FOOT)
    r.txt(col_a, fy - 3.5*mm,  "Bank  : Karur Vysya Bank",     font=FB, size=SZ_FOOT)
    r.txt(col_a, fy - 7.0*mm,  "A/c : 1120 135 00 001 618",              size=SZ_FOOT)

    r.txt(col_b, fy,           "IFSC : KVBL 000 1120",          font=FB, size=SZ_FOOT)
    r.txt(col_b, fy - 3.5*mm,  "Branch : Coimbatore Main Br.",            size=SZ_FOOT)
    r.txt(col_b, fy - 7.0*mm,  "GPay : 80156 14944",            font=FB, size=SZ_FOOT)

    # Signature box (right 40%)
    sig_x = BL + BANK_W
    r.box(sig_x, y, SIG_W, FH, lw=0.5)
    sig_mid = y - FH / 2
    r.txt(sig_x + SIG_W/2, sig_mid + 1.5*mm,
          "Sign. / Rubber Stamp of Consignee",
          size=5.0, align="center")
    r.txt(sig_x + SIG_W/2, sig_mid - 2.5*mm,
          "For S A Salem Super Service",
          font=FB, size=5.5, align="center")

    # Bottom border
    r.hline(r.PAD, PW - r.PAD, r.PAD + 0.3*mm, lw=1.2)


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def generate_courier_pdf(courier: dict) -> BytesIO:
    """
    Generate a half-A4 Lorry Way Bill PDF and return as BytesIO.

    courier keys:  invoice_number, date,
      from_location, to_location,
      sender_name, sender_phone_num, from_address,
      receiver_name, receiver_phone_num, to_address,
      no_of_packages, weight, delivery_type,
      parcel_information  → list of [name, qty],
      freight, loading_unloading, door_pickup, dd_charges,
      other_transport_crossing, mamool, statistical_charges,
      total,
      payment_status  → 'PAID' | 'TO PAY' | 'RTN',
      booked_by
    """
    buf = BytesIO()
    r   = Renderer(buf)

    y = draw_header(r, courier.get("invoice_number", ""))
    y = draw_waybill_bar(r, y)
    y = draw_body(r, y, courier)
    draw_footer(r, y)   # footer always starts where body ended

    r.save()
    buf.seek(0)
    return buf


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════════

# if __name__ == "__main__":
#     import os
#     sample = {
#         "invoice_number": "50293",
#         "date": "11-05-2026",
#         "from_location": "Coimbatore",
#         "to_location": "Salem",
#         "sender_name": "Ravi Kumar",
#         "sender_phone_num": "98765 43210",
#         "from_address": "12, Anna Nagar, Coimbatore - 641001",
#         "receiver_name": "Suresh Babu",
#         "receiver_phone_num": "87654 32109",
#         "to_address": "45, Gandhi Road, Salem - 636002",
#         "no_of_packages": "3",
#         "weight": "12.5",
#         "delivery_type": "Godown",
#         "parcel_information": [["Electronics", "2"], ["Clothes", "1"]],
#         "freight": 350,
#         "loading_unloading": 50,
#         "door_pickup": 0,
#         "dd_charges": 0,
#         "other_transport_crossing": 10,
#         "mamool": 0,
#         "statistical_charges": 10,
#         "total": 420,
#         "payment_status": "TO PAY",
#         "booked_by": "Karthik",
#     }
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     output_path = os.path.join(script_dir, "madras_cargo_waybill.pdf")
#     buf = generate_courier_pdf(sample)
#     with open(output_path, "wb") as f:
#         f.write(buf.read())
#     print(f"Saved to: {output_path}")


def format_phone(phone):
    phone = str(phone).strip()
    if len(phone) == 10 and phone.isdigit():
        return f"+91{phone}"
    return phone

def send_sms(to_number, body):
    """
    Sends an SMS message using Twilio.
    """
    to_number = format_phone(to_number)
    print(f"Attempting to send SMS to {to_number}...")
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_number
        )
        print(f"SMS sent successfully! SID: {message.sid}")
        return message.sid
    except Exception as e:
        print(f"Error sending SMS to {to_number}: {e}")
        return None




import os
from io import BytesIO
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib import colors

class GDMReceiptGenerator:
    """
    Encapsulates all logic, constants, and drawing primitives for generating 
    the S A Salem Super Service GDM Receipt PDF to prevent global scope contamination.
    """
    
    # ── Page Dimensions ───────────────────────────────────────────────────────
    PW = 210 * mm      # A4 width
    PH = 297 * mm      # A4 height

    # ── Color Palette ─────────────────────────────────────────────────────────
    C_BLACK = colors.HexColor("#000000")
    C_DARK = colors.HexColor("#1A237E")     # dark navy (accent)
    C_GREY = colors.HexColor("#666666")
    C_LTGREY = colors.HexColor("#999999")
    C_BGLIGHT = colors.HexColor("#F5F5F5")   # light grey for header rows
    C_WHITE = colors.white

    # ── Typography Scale ──────────────────────────────────────────────────────
    FB = "Helvetica-Bold"
    FR = "Helvetica"
    FI = "Helvetica-Oblique"
    FBI = "Helvetica-BoldOblique"

    SZ_COMPANY = 18       # company name
    SZ_TAGLINE = 6.5      # tagline
    SZ_ADDR = 5.0         # company address
    SZ_RECEIPT = 14       # "GDM RECEIPT"
    SZ_META_LBL = 5.5     # metadata labels (GDM Number, Date, etc.)
    SZ_META_VAL = 10      # metadata values (GDM number)
    SZ_META_SM = 6.5      # smaller metadata values (date, route)
    SZ_SEC_HDR = 7.0      # section heading ("Consignment Ledger")
    SZ_TH = 7.5           # table header
    SZ_TD = 8.0           # table data
    SZ_TD_TINY = 5.5      # tiny sub-text in table
    SZ_TOT_LBL = 8.5      # total row label
    SZ_TOT_VAL = 8.5      # total row value
    SZ_SIG = 6.0          # signature text
    SZ_SIG_SUB = 5.0      # signature sub-text

    # ── Spacing Constants ─────────────────────────────────────────────────────
    MARGIN = 12 * mm    # page margin
    HP = 2.5 * mm       # horizontal cell padding
    VP = 2.0 * mm       # vertical cell padding
    ROW_H = 9.5 * mm    # table body row height
    HDR_ROW_H = 9.0 * mm   # table header row height
    TOT_ROW_H = 10.0 * mm  # total row height
    BORDER_W = 0.5         # default border line width
    THICK_W = 2.0          # thick border for header separator
    FOOTER_RESERVE = 50 * mm # space reserved for footer + signature blocks

    class _LocalRenderer:
        """Isolated structural canvas context wrapper."""
        def __init__(self, buf, outer):
            self.outer = outer
            self.c = rl_canvas.Canvas(buf, pagesize=(outer.PW, outer.PH))
            self.PAD = outer.MARGIN
            self.BL = self.PAD            
            self.BR = outer.PW - self.PAD       
            self.BW = self.BR - self.BL   

        def hline(self, x1, x2, y, lw=None, color=None):
            self.c.setStrokeColor(color or self.outer.C_BLACK)
            self.c.setLineWidth(lw or self.outer.BORDER_W)
            self.c.line(x1, y, x2, y)

        def vline(self, x, y1, y2, lw=None, color=None):
            self.c.setStrokeColor(color or self.outer.C_BLACK)
            self.c.setLineWidth(lw or self.outer.BORDER_W)
            self.c.line(x, y1, x, y2)

        def box(self, x, y_top, w, h, lw=None, fill=None, color=None):
            self.c.setStrokeColor(color or self.outer.C_BLACK)
            self.c.setLineWidth(lw or self.outer.BORDER_W)
            if fill:
                self.c.setFillColor(fill)
                self.c.rect(x, y_top - h, w, h, stroke=1, fill=1)
            else:
                self.c.rect(x, y_top - h, w, h, stroke=1, fill=0)

        def txt(self, x, y, s, font=None, size=7, color=None, align="left"):
            self.c.setFont(font or self.outer.FR, size)
            self.c.setFillColor(color or self.outer.C_BLACK)
            s = str(s)
            if align == "center": self.c.drawCentredString(x, y, s)
            elif align == "right":  self.c.drawRightString(x, y, s)
            else:                   self.c.drawString(x, y, s)

        def sw(self, s, font, size):
            return self.c.stringWidth(str(s), font, size)

        def wrap(self, text, font, size, max_w):
            words = str(text).split()
            if not words: return [""]
            lines, cur = [], words[0]
            for w in words[1:]:
                test = cur + " " + w
                if self.sw(test, font, size) <= max_w:
                    cur = test
                else:
                    lines.append(cur)
                    cur = w
            lines.append(cur)
            return lines

        def save(self):
            self.c.showPage()
            self.c.save()

    @classmethod
    def _draw_header(cls, r: _LocalRenderer, d: dict) -> float:
        top = cls.PH - r.PAD

        # ── Company info (left) ───────────────────────────────────────────────
        r.txt(r.BL, top - 7 * mm, "S A Salem Super Service",
              font=cls.FB, size=cls.SZ_COMPANY, color=cls.C_BLACK)

        addr_text = d.get("company_address", "REGULAR PARCEL SERVICE")
        addr_lines = r.wrap(addr_text, cls.FR, cls.SZ_ADDR, 60 * mm)
        ay = top - 13 * mm
        for ln in addr_lines:
            r.txt(r.BL, ay, ln, font=cls.FR, size=cls.SZ_ADDR, color=cls.C_LTGREY)
            ay -= 2.5 * mm

        # ── GDM Receipt info (right) ──────────────────────────────────────────
        r.txt(r.BR, top - 8 * mm, "GDM RECEIPT",
              font=cls.FB, size=cls.SZ_RECEIPT, color=cls.C_BLACK, align="right")

        r.txt(r.BR, top - 14 * mm, "GDM Number",
              font=cls.FB, size=cls.SZ_META_LBL, color=cls.C_LTGREY, align="right")
        r.txt(r.BR, top - 19 * mm, str(d.get("gdm_no", "")),
              font=cls.FB, size=cls.SZ_META_VAL, color=cls.C_BLACK, align="right")

        r.txt(r.BR, top - 24 * mm, "Dispatch Date",
              font=cls.FB, size=cls.SZ_META_LBL, color=cls.C_LTGREY, align="right")
        r.txt(r.BR, top - 28 * mm, str(d.get("dispatch_date", "")),
              font=cls.FB, size=cls.SZ_META_SM, color=cls.C_GREY, align="right")

        route_y = top - 33 * mm
        r.txt(r.BR, route_y, f"Route: {d.get('route', '')}",
              font=cls.FB, size=cls.SZ_META_SM, color=cls.C_DARK, align="right")
        r.txt(r.BR, route_y - 3.5 * mm, f"Vehicle: {d.get('vehicle_no', '')}",
              font=cls.FB, size=cls.SZ_META_SM, color=cls.C_DARK, align="right")
        r.txt(r.BR, route_y - 7.0 * mm, f"Driver: {d.get('driver_name', '')}",
              font=cls.FB, size=cls.SZ_META_SM, color=cls.C_DARK, align="right")

        sep_y = top - 42 * mm
        r.hline(r.BL, r.BR, sep_y, lw=cls.THICK_W)
        return sep_y

    @classmethod
    def _new_page(cls, r: _LocalRenderer):
        r.c.showPage()
        r.c.setFillColor(cls.C_WHITE)
        r.c.rect(0, 0, cls.PW, cls.PH, stroke=0, fill=1)

    @classmethod
    def _draw_table_header(cls, r, y, col_widths, col_headers, col_aligns):
        r.box(r.BL, y, r.BW, cls.HDR_ROW_H, lw=cls.BORDER_W, fill=cls.C_BGLIGHT)
        cx = r.BL
        for i, (w, hdr, aln) in enumerate(zip(col_widths, col_headers, col_aligns)):
            if i > 0:
                r.vline(cx, y, y - cls.HDR_ROW_H)
            ty = y - cls.HDR_ROW_H + (cls.HDR_ROW_H - cls.SZ_TH * 0.352) / 2
            if aln == "center":
                r.txt(cx + w / 2, ty, hdr, font=cls.FB, size=cls.SZ_TH, align="center")
            elif aln == "right":
                r.txt(cx + w - cls.HP, ty, hdr, font=cls.FB, size=cls.SZ_TH, align="right")
            else:
                r.txt(cx + cls.HP, ty, hdr, font=cls.FB, size=cls.SZ_TH)
            cx += w
        r.hline(r.BL, r.BR, y - cls.HDR_ROW_H)
        return y - cls.HDR_ROW_H

    @classmethod
    def _draw_consignment_table(cls, r: _LocalRenderer, y: float, d: dict) -> float:
        SAFE_BOT = r.PAD + cls.FOOTER_RESERVE

        y -= 6 * mm
        r.c.setFillColor(cls.C_BLACK)
        r.c.rect(r.BL, y - 4 * mm, 1.5 * mm, 4 * mm, stroke=0, fill=1)
        r.txt(r.BL + 4 * mm, y - 3 * mm, "Consignment Ledger", font=cls.FB, size=cls.SZ_SEC_HDR)
        y -= 8 * mm

        COL_SNO = r.BW * 0.08
        COL_LR = r.BW * 0.18
        COL_PACK = r.BW * 0.44
        COL_PKGS = r.BW * 0.15
        COL_FRT = r.BW * 0.15
        col_widths = [COL_SNO, COL_LR, COL_PACK, COL_PKGS, COL_FRT]
        col_headers = ["S.No", "LR Number", "Nature of Packing", "No. of Pkgs", "Freight"]
        col_aligns = ["center", "left", "left", "center", "right"]

        y = cls._draw_table_header(r, y, col_widths, col_headers, col_aligns)

        bookings = d.get("bookings", [])
        for idx, lr in enumerate(bookings):
            if y - cls.ROW_H < SAFE_BOT:
                cls._new_page(r)
                y = cls.PH - r.PAD - 6 * mm
                r.txt(r.BL, y, "Consignment Ledger (contd.)", font=cls.FB, size=cls.SZ_SEC_HDR)
                y -= 6 * mm
                y = cls._draw_table_header(r, y, col_widths, col_headers, col_aligns)

            r.box(r.BL, y, r.BW, cls.ROW_H, lw=cls.BORDER_W)
            cx = r.BL
            for i, w in enumerate(col_widths):
                if i > 0: r.vline(cx, y, y - cls.ROW_H)
                cx += w

            ty = y - cls.ROW_H + (cls.ROW_H - cls.SZ_TD * 0.352) / 2

            # S.No
            r.txt(r.BL + col_widths[0] / 2, ty, str(idx + 1), font=cls.FB, size=cls.SZ_TD, align="center")
            cx = r.BL + col_widths[0]

            # LR Number + payment mode
            r.txt(cx + cls.HP, ty + 1.2 * mm, str(lr.get("lr_no", "")), font=cls.FB, size=cls.SZ_TD)
            payment_mode = lr.get("payment_mode", "")
            if payment_mode:
                r.txt(cx + cls.HP, ty - 2.2 * mm, f"Paid via {payment_mode}", font=cls.FI, size=cls.SZ_TD_TINY, color=cls.C_LTGREY)
            cx += col_widths[1]

            # Nature of Packing
            pack_name = str(lr.get("package_name", "General Parcel"))
            r.txt(cx + cls.HP, ty, pack_name.upper(), font=cls.FR, size=cls.SZ_TD)
            cx += col_widths[2]

            # No. of Pkgs
            pkgs = str(lr.get("travellers_count", 1))
            r.txt(cx + col_widths[3] / 2, ty, pkgs, font=cls.FB, size=cls.SZ_TD, align="center")
            cx += col_widths[3]

            # Freight
            total_price = lr.get("total_price", 0)
            r.txt(cx + col_widths[4] - cls.HP, ty,
                  f"Rs.{total_price:,.0f}" if isinstance(total_price, (int, float)) else str(total_price),
                  font=cls.FB, size=cls.SZ_TD, align="right")

            y -= cls.ROW_H

        if y - cls.TOT_ROW_H < SAFE_BOT:
            cls._new_page(r)
            y = cls.PH - r.PAD - 6 * mm

        r.box(r.BL, y, r.BW, cls.TOT_ROW_H, lw=cls.BORDER_W, fill=cls.C_BGLIGHT)
        tot_cx = r.BL
        for i, w in enumerate(col_widths):
            if i > 0: r.vline(tot_cx, y, y - cls.TOT_ROW_H)
            tot_cx += w

        tot_ty = y - cls.TOT_ROW_H + (cls.TOT_ROW_H - cls.SZ_TOT_VAL * 0.352) / 2
        span_w = col_widths[0] + col_widths[1] + col_widths[2]
        r.txt(r.BL + span_w - cls.HP, tot_ty, "Total Summary", font=cls.FB, size=cls.SZ_TOT_LBL, align="right")

        total_pkgs = str(d.get("total_packages", 0))
        r.txt(r.BL + span_w + col_widths[3] / 2, tot_ty, f"{total_pkgs} Pkgs", font=cls.FB, size=cls.SZ_TOT_VAL, align="center")

        total_freight = d.get("total_freight", 0)
        r.txt(r.BR - cls.HP, tot_ty,
              f"Rs.{total_freight:,.0f}" if isinstance(total_freight, (int, float)) else str(total_freight),
              font=cls.FB, size=cls.SZ_TOT_VAL, align="right")

        r.hline(r.BL, r.BR, y - cls.TOT_ROW_H, lw=cls.BORDER_W)
        return y - cls.TOT_ROW_H

    @classmethod
    def _draw_footer(cls, r: _LocalRenderer, y: float):
        SIG_GAP = 25 * mm   
        SIG_W = (r.BW - SIG_GAP) / 2
        SIG_TOP_Y = y - 30 * mm  

        # Left Signature
        r.hline(r.BL, r.BL + SIG_W, SIG_TOP_Y)
        r.txt(r.BL + SIG_W / 2, SIG_TOP_Y - 5 * mm, "Dispatch Manager Signature", font=cls.FB, size=cls.SZ_SIG, align="center")
        r.txt(r.BL + SIG_W / 2, SIG_TOP_Y - 9 * mm, "Auth ID: EMP-90218", font=cls.FI, size=cls.SZ_SIG_SUB, color=cls.C_LTGREY, align="center")

        # Right Signature
        rx = r.BR - SIG_W
        r.hline(rx, rx + SIG_W, SIG_TOP_Y)
        r.txt(rx + SIG_W / 2, SIG_TOP_Y - 5 * mm, "Driver's Acknowledgement", font=cls.FB, size=cls.SZ_SIG, align="center")
        r.txt(rx + SIG_W / 2, SIG_TOP_Y - 9 * mm, "Verify vehicle seal before signing", font=cls.FI, size=cls.SZ_SIG_SUB, color=cls.C_LTGREY, align="center")

    @classmethod
    def generate_pdf(cls, gdm_data: dict) -> BytesIO:
        """
        Public execution entry point. Allocates buffer components locally 
        and maps pipeline transformations inside structural layouts.
        """
        buf = BytesIO()
        r = cls._LocalRenderer(buf, cls)

        # Base frame setup
        r.c.setFillColor(cls.C_WHITE)
        r.c.rect(0, 0, cls.PW, cls.PH, stroke=0, fill=1)

        # Border shadow card overlay representation
        r.box(r.PAD - 1 * mm, cls.PH - r.PAD + 1 * mm,
              cls.PW - 2 * r.PAD + 2 * mm, cls.PH - 2 * r.PAD + 2 * mm,
              lw=0.3, color=colors.HexColor("#E5E7EB"))

        y_cursor = cls._draw_header(r, gdm_data)
        y_cursor = cls._draw_consignment_table(r, y_cursor, gdm_data)
        cls._draw_footer(r, y_cursor)

        r.save()
        buf.seek(0)
        return buf

# ── Backwards Compatible Global Alias Pointer ─────────────────────────────────
def generate_gdm_pdf(gdm: dict) -> BytesIO:
    return GDMReceiptGenerator.generate_pdf(gdm)


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO EXECUTION STRATUM
# ═══════════════════════════════════════════════════════════════════════════════
# if __name__ == "__main__":
#     sample = {
#         "gdm_no": "GDM-2026-0047",
#         "dispatch_date": "02-06-2026",
#         "route": "Chennai → Salem",
#         "vehicle_no": "TN-09-AB-1234",
#         "driver_name": "Murugan K",
#         "total_packages": 12,
#         "total_freight": 18500,
#         "bookings": [
#             {"lr_no": "LR-50293", "payment_mode": "Cash", "package_name": "Electronics", "travellers_count": 3, "total_price": 4500},
#             {"lr_no": "LR-50294", "payment_mode": "UPI", "package_name": "Textiles", "travellers_count": 5, "total_price": 7200},
#             {"lr_no": "LR-50295", "payment_mode": "", "package_name": "Machinery Parts", "travellers_count": 2, "total_price": 3800},
#             {"lr_no": "LR-50296", "payment_mode": "Credit", "package_name": "General Parcel", "travellers_count": 2, "total_price": 3000},
#         ],
#     }

#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     output_path = os.path.join(script_dir, "gdm_receipt.pdf")
    
#     # Executing through encapsulated namespace logic
#     pdf_buffer = GDMReceiptGenerator.generate_pdf(sample)
    
#     with open(output_path, "wb") as f:
#         f.write(pdf_buffer.read())
#     print(f"Successfully saved to: {output_path}")