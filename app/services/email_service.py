import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path

from core.config import settings


# ======================================================
# 🔧 SMTP CONFIG (Updated based on your env names)
# ======================================================
SMTP_HOST = settings.EMAIL_HOST
SMTP_PORT = settings.EMAIL_PORT
SMTP_USER = settings.EMAIL_USERNAME
SMTP_PASSWORD = settings.EMAIL_PASSWORD

# if EMAIL_FROM not in env, fallback to EMAIL_USERNAME
FROM_EMAIL = getattr(settings, "EMAIL_FROM", SMTP_USER)


# ======================================================
# 🔹 BASE HTML EMAIL SENDER
# ======================================================
def send_html_email(
    to_email: str,
    subject: str,
    html_body: str,
    attachment_path: str | None = None,
):
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError("Email credentials not loaded from .env")

    msg = MIMEMultipart()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(html_body, "html"))

    # ✅ attachment support
    if attachment_path:
        file_path = Path(attachment_path)
        if file_path.exists():
            with open(file_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=file_path.name)
            part["Content-Disposition"] = f'attachment; filename="{file_path.name}"'
            msg.attach(part)

    # ✅ SMTP send
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


# ======================================================
# 📦 COMMON OTP TEMPLATE (AUTH + DELIVERY)
# ======================================================
def _otp_email_template(name: str, otp: str, purpose: str) -> str:
    return f"""
    <html>
    <body style="margin:0;background:#f4f6f8;font-family:Arial,Helvetica,sans-serif">
        <div style="max-width:600px;margin:auto;background:#ffffff;border-radius:8px;overflow:hidden">

            <div style="background:#0b5c6b;color:white;padding:20px;text-align:center">
                <h2 style="margin:0">ANAND PHARMA</h2>
                <p style="margin:5px 0 0;font-size:13px">Trusted Healthcare</p>
            </div>

            <div style="padding:30px;color:#333">
                <p>Hello <b>{name}</b>,</p>

                <p>
                    Please use the One-Time Password (OTP) below to complete
                    <b>{purpose}</b>.
                </p>

                <div style="text-align:center;margin:30px 0">
                    <div style="
                        display:inline-block;
                        padding:15px 35px;
                        background:#0b5c6b;
                        color:white;
                        font-size:26px;
                        border-radius:8px;
                        letter-spacing:6px;
                        font-weight:bold;
                    ">
                        {otp}
                    </div>
                </div>

                <p style="font-size:14px">
                    This OTP is valid for <b>10 minutes</b>.
                </p>

                <p style="font-size:14px;color:#666">
                    If you did not initiate this request, please ignore this email.
                </p>

                <br>

                <p style="font-size:14px">
                    Warm regards,<br>
                    <b>Anand Pharma Team</b>
                </p>
            </div>

            <div style="text-align:center;padding:12px;color:#999;font-size:12px;background:#fafafa">
                © 2026 Anand Pharma. All Rights Reserved.
            </div>

        </div>
    </body>
    </html>
    """


# ======================================================
# 🔐 AUTH OTP EMAIL
# ======================================================
def send_auth_otp_email(email: str, name: str, otp: str):
    send_html_email(
        to_email=email,
        subject="Email Verification OTP – Anand Pharma",
        html_body=_otp_email_template(name, otp, "email verification"),
    )


def resend_auth_otp_email(email: str, name: str, otp: str):
    send_html_email(
        to_email=email,
        subject="Resent OTP – Anand Pharma",
        html_body=_otp_email_template(name, otp, "email verification"),
    )


# ======================================================
# 📲 DELIVERY OTP EMAIL
# ======================================================
def send_delivery_otp_email(email: str, name: str, otp: str):
    send_html_email(
        to_email=email,
        subject="Delivery OTP – Anand Pharma",
        html_body=_otp_email_template(name, otp, "delivery confirmation"),
    )


def resend_delivery_otp_email(email: str, name: str, otp: str):
    send_html_email(
        to_email=email,
        subject="Resent Delivery OTP – Anand Pharma",
        html_body=_otp_email_template(name, otp, "delivery confirmation"),
    )


# ======================================================
# 🚴 DELIVERY AGENT ASSIGNMENT EMAIL
# ======================================================
def send_delivery_assignment_email(email: str, order_id: int):
    html = f"""
    <html>
    <body style="font-family:Arial,Helvetica,sans-serif;background:#f4f6f8;padding:20px">
        <div style="max-width:600px;margin:auto;background:#ffffff;padding:30px;border-radius:8px">

            <h2 style="color:#0b5c6b">🚚 New Delivery Assigned</h2>

            <p>You have been assigned a new delivery task.</p>

            <div style="background:#f1f5f9;padding:15px;border-radius:6px;margin:20px 0">
                <p style="margin:0"><b>Order ID:</b> #{order_id}</p>
            </div>

            <p>
                Please open the <b>Anand Pharma Delivery App</b> to view pickup
                and delivery details and complete the order.
            </p>

            <p style="margin-top:20px;font-size:14px;color:#555">
                Ensure timely and safe delivery as per company guidelines.
            </p>

            <hr style="margin:30px 0">

            <p style="font-size:13px;color:#777">
                Anand Pharma Logistics Team<br>
                Trusted Healthcare Delivery
            </p>
        </div>
    </body>
    </html>
    """

    send_html_email(
        to_email=email,
        subject=f"New Delivery Assigned | Order #{order_id}",
        html_body=html,
    )


# ======================================================
# 🧾 INVOICE EMAIL (POST DELIVERY)
# ======================================================
def send_invoice_email(email: str, order_id: int, invoice_path: str):
    html = f"""
    <html>
    <body style="font-family:Arial,Helvetica,sans-serif;background:#f4f6f8;padding:20px">
        <div style="max-width:600px;margin:auto;background:#ffffff;padding:30px;border-radius:8px">

            <h2 style="color:#0b5c6b">🧾 Invoice & Delivery Confirmation</h2>

            <p>
                Thank you for choosing <b>Anand Pharma</b>.
            </p>

            <p>
                Your order <b>#{order_id}</b> has been successfully delivered.
            </p>

            <div style="background:#f1f5f9;padding:15px;border-radius:6px;margin:20px 0">
                <p style="margin:0">
                    The attached invoice includes:
                </p>
                <ul style="font-size:14px;margin:10px 0">
                    <li>Medicine details & quantities</li>
                    <li>Price breakdown</li>
                    <li>CGST & SGST</li>
                    <li>Total amount paid</li>
                </ul>
            </div>

            <p style="font-size:14px;color:#555">
                If you have any questions, our support team will be happy to assist you.
            </p>

            <hr style="margin:30px 0">

            <p style="font-size:13px;color:#777">
                Stay healthy,<br>
                <b>Anand Pharma Team</b><br>
                Trusted Healthcare
            </p>
        </div>
    </body>
    </html>
    """

    send_html_email(
        to_email=email,
        subject=f"Invoice & Delivery Confirmation | Order #{order_id}",
        html_body=html,
        attachment_path=invoice_path,
    )
