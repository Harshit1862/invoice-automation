"""
Generates a small set of synthetic invoice PDFs covering the exception
categories our decision engine needs to handle. Run once to populate
data/invoices/ with a realistic test set.

Usage: python scripts/generate_synthetic_invoices.py
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

OUT_DIR = "data/invoices"


def draw_invoice(filename, vendor, invoice_number, invoice_date, po_number,
                  line_items, total, note=None):
    """line_items: list of (description, qty, unit_price, line_total) tuples"""
    path = os.path.join(OUT_DIR, filename)
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    y = height - 72

    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, vendor)
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(72, y, f"Invoice #: {invoice_number}")
    y -= 14
    c.drawString(72, y, f"Date: {invoice_date}")
    y -= 14
    c.drawString(72, y, f"PO Number: {po_number if po_number else '(none provided)'}")
    y -= 30

    c.setFont("Helvetica-Bold", 10)
    c.drawString(72, y, "Description")
    c.drawString(320, y, "Qty")
    c.drawString(380, y, "Unit Price")
    c.drawString(470, y, "Line Total")
    y -= 16
    c.line(72, y, 540, y)
    y -= 14

    c.setFont("Helvetica", 10)
    for desc, qty, price, line_total in line_items:
        c.drawString(72, y, desc)
        c.drawString(320, y, str(qty))
        c.drawString(380, y, f"${price:,.2f}")
        c.drawString(470, y, f"${line_total:,.2f}")
        y -= 16

    y -= 10
    c.line(72, y, 540, y)
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(400, y, f"Total: ${total:,.2f}")

    if note:
        y -= 30
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(72, y, note)

    c.save()
    print(f"created {path}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1. Clean match -- should auto-approve against PO-1001 ($12,000.00)
    draw_invoice(
        "inv_clean_match.pdf",
        vendor="Acme Office Supplies",
        invoice_number="ACM-8841",
        invoice_date="2026-06-02",
        po_number="PO-1001",
        line_items=[("Standing desks, qty 20", 20, 500.00, 10000.00),
                    ("Ergonomic chairs, qty 20", 20, 100.00, 2000.00)],
        total=12000.00,
    )

    # 2. Borderline -- within 2% tolerance against PO-1005 ($1,560.00), should auto-approve
    draw_invoice(
        "inv_within_tolerance.pdf",
        vendor="Acme Office Supplies",
        invoice_number="ACM-8842",
        invoice_date="2026-06-03",
        po_number="PO-1005",
        line_items=[("Printer paper, 50 boxes", 50, 31.50, 1575.00)],
        total=1575.00,  # ~0.96% over PO amount
    )

    # 3. Amount mismatch -- 12% over PO-1002 ($8,450.50), should flag
    draw_invoice(
        "inv_amount_mismatch.pdf",
        vendor="Beacon Logistics Inc",
        invoice_number="BLI-2201",
        invoice_date="2026-06-04",
        po_number="PO-1002",
        line_items=[("Freight - June shipment", 1, 9464.56, 9464.56)],
        total=9464.56,
        note="Note: fuel surcharge applied, not reflected on original PO",
    )

    # 4. No PO number present -- should flag
    draw_invoice(
        "inv_missing_po.pdf",
        vendor="Crestview Consulting",
        invoice_number="CVC-0099",
        invoice_date="2026-06-05",
        po_number=None,
        line_items=[("Strategy advisory, June", 1, 25000.00, 25000.00)],
        total=25000.00,
    )

    # 5. Vendor not on file -- should flag
    draw_invoice(
        "inv_unknown_vendor.pdf",
        vendor="Northline Data Systems",
        invoice_number="NDS-1150",
        invoice_date="2026-06-06",
        po_number="PO-9999",
        line_items=[("Server maintenance contract", 1, 3200.00, 3200.00)],
        total=3200.00,
    )

    # 6. Duplicate invoice number -- same number as inv_clean_match, should flag
    draw_invoice(
        "inv_duplicate.pdf",
        vendor="Acme Office Supplies",
        invoice_number="ACM-8841",
        invoice_date="2026-06-10",
        po_number="PO-1001",
        line_items=[("Standing desks, qty 20", 20, 500.00, 10000.00),
                    ("Ergonomic chairs, qty 20", 20, 100.00, 2000.00)],
        total=12000.00,
        note="Resubmission of invoice ACM-8841",
    )


if __name__ == "__main__":
    main()