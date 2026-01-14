from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
from pathlib import Path

INVOICE_DIR = "invoices"
Path(INVOICE_DIR).mkdir(exist_ok=True)


def generate_gst_invoice(order, items):
    file_path = f"{INVOICE_DIR}/invoice_order_{order.id}.pdf"
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    y = height - 50

    # 🏥 Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "ANAND PHARMA")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Trusted Healthcare")
    y -= 30

    # 🧾 Invoice info
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Invoice No: INV-{order.id}")
    c.drawString(350, y, f"Date: {datetime.now().strftime('%d-%m-%Y')}")
    y -= 20

    c.drawString(50, y, f"Customer ID: {order.user_id}")
    y -= 30

    # 🧾 Table Header
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Product")
    c.drawString(260, y, "Qty")
    c.drawString(300, y, "Price")
    c.drawString(360, y, "Total")
    y -= 15
    c.line(50, y, 550, y)
    y -= 15

    # 🧾 Items
    c.setFont("Helvetica", 10)
    subtotal = 0

    for item in items:
        line_total = item.price * item.quantity
        subtotal += line_total

        c.drawString(50, y, item.product_name)
        c.drawString(260, y, str(item.quantity))
        c.drawString(300, y, f"{item.price:.2f}")
        c.drawString(360, y, f"{line_total:.2f}")
        y -= 20

        if y < 100:
            c.showPage()
            y = height - 50

    # 🧮 GST Calculation
    cgst = subtotal * 0.09
    sgst = subtotal * 0.09
    total = subtotal + cgst + sgst

    y -= 20
    c.line(300, y, 550, y)
    y -= 15

    c.drawString(300, y, "Subtotal:")
    c.drawString(430, y, f"{subtotal:.2f}")
    y -= 15

    c.drawString(300, y, "CGST (9%):")
    c.drawString(430, y, f"{cgst:.2f}")
    y -= 15

    c.drawString(300, y, "SGST (9%):")
    c.drawString(430, y, f"{sgst:.2f}")
    y -= 15

    c.setFont("Helvetica-Bold", 10)
    c.drawString(300, y, "Grand Total:")
    c.drawString(430, y, f"{total:.2f}")

    # Footer
    y -= 40
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "This is a computer generated invoice.")

    c.save()
    return file_path
