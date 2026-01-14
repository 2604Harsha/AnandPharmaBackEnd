from datetime import datetime
from fastapi import APIRouter, Depends, Response, HTTPException, Request, status
from fastapi import security
from fastapi.security import HTTPBasicCredentials, HTTPBearer
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.password_reset import PasswordResetToken
from core.security import hash_password
from models.user import User
from models.email_otp import EmailOTP
from services.email_service import send_html_email
from services.email_service import send_auth_otp_email, resend_auth_otp_email
from utils.otp import generate_otp
from schemas.user import ResetPasswordRequest, UserCreate, UserLogin
from services.auth_service import create_user, authenticate_user
from utils.jwt import create_access_token
from core.database import get_db
from core.rbac import require_role

router = APIRouter(prefix="/auth", tags=["Auth"])

swagger_security = HTTPBearer()

# ======================================================
# ✅ USER REGISTER
# ======================================================
@router.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):

    if user.role != "user":
        raise HTTPException(
            status_code=403,
            detail="Only USER role can register"
        )

    new_user = await create_user(db, user)

    otp = generate_otp()

    db.add(
        EmailOTP(
            user_id=new_user.id,
            otp=otp,
            expires_at=EmailOTP.expiry_time()
        )
    )
    await db.commit()

    # ✅ New Template Mail
    send_auth_otp_email(
        email=new_user.email,
        name=new_user.full_name or "User",
        otp=otp
    )

    return {
        "message": "Registration successful. Verification OTP sent to email.",
        "status": "NOT VERIFIED"
    }


# ======================================================
# ✅ VERIFY OTP
# ======================================================
@router.post("/verify-otp")
async def verify_otp(
    email: str,
    otp: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(EmailOTP).where(
            and_(
                EmailOTP.user_id == user.id,
                EmailOTP.otp == otp,
                EmailOTP.expires_at > datetime.utcnow()
            )
        )
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user.is_verified = True
    await db.commit()

    return {
        "message": "Email verified successfully",
        "status": "ACTIVE"
    }


# ======================================================
# ✅ RESEND OTP
# ======================================================
@router.post("/resend-otp")
async def resend_otp(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    # 🔍 Check user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Already verified
    if user.is_verified:
        return {"message": "Email already verified"}

    # 🔥 Delete old OTPs
    await db.execute(delete(EmailOTP).where(EmailOTP.user_id == user.id))

    # 🔐 Generate new OTP
    otp = generate_otp()

    db.add(
        EmailOTP(
            user_id=user.id,
            otp=otp,
            expires_at=EmailOTP.expiry_time()
        )
    )
    await db.commit()

    # ✅ New Template Mail
    resend_auth_otp_email(
        email=user.email,
        name=user.full_name or "User",
        otp=otp
    )

    return {"message": "OTP resent successfully"}


# ======================================================
# ✅ STAFF CREATE (ADMIN ONLY)
# ======================================================
@router.post("/staff-create")
async def staff_create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("ADMIN")),
):
    if user.role not in ["pharmacist", "delivery_agent"]:
        raise HTTPException(
            status_code=400,
            detail="Admin can only create Pharmacist or Delivery Agent"
        )

    # Create user
    new_user = await create_user(db, user)

    # Generate OTP
    otp = generate_otp()

    db.add(
        EmailOTP(
            user_id=new_user.id,
            otp=otp,
            expires_at=EmailOTP.expiry_time()
        )
    )
    await db.commit()

    # ✅ New Template Mail
    send_auth_otp_email(
        email=new_user.email,
        name=new_user.full_name or user.role.replace("_", " ").title(),
        otp=otp
    )

    return {
        "message": f"{user.role} account created successfully",
        "status": "NOT VERIFIED",
        "role": user.role
    }


# ======================================================
# ✅ ADMIN BASIC AUTH (OPTIONAL)
# ======================================================
def admin_basic_auth(
    credentials: HTTPBasicCredentials = Depends(security)
):
    if (
        credentials.username != "admin@pharma.com"
        or credentials.password != "Admin@123"
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


# ======================================================
# ✅ LOGIN
# ======================================================
@router.post("/login")
async def login(
    data: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Login for all users (Admin, Pharmacist, Delivery Agent, User)
    """

    user = await authenticate_user(db, data.email, data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax"
    )

    return {
        "message": "Login successful",
        "role": user.role,
        "user_id":user.id,
        "token": token
    }


# ======================================================
# ✅ FORGOT PASSWORD (RESET LINK EMAIL)
# ======================================================
@router.post("/forgot-password")
async def forgot_password(email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = PasswordResetToken.generate_token()

    db.add(
        PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=PasswordResetToken.expiry_time()
        )
    )
    await db.commit()

    reset_link = f"http://localhost:3000/reset-password?token={token}"

    # ✅ Keep send_html_email because this is not OTP template
    email_body = f"""
    <html>
    <body style="font-family:Arial,Helvetica,sans-serif;background:#f4f6f8;padding:20px">
        <div style="max-width:600px;margin:auto;background:#ffffff;padding:30px;border-radius:8px">

            <h2 style="color:#0b5c6b">🔐 Password Reset Request</h2>

            <p>Hello <b>{user.full_name or "User"}</b>,</p>

            <p>We received a request to reset the password for your account.</p>

            <p>Click the button below to reset your password:</p>

            <div style="margin:20px 0;text-align:center">
                <a href="{reset_link}" style="
                    background:#0b5c6b;
                    color:white;
                    padding:12px 25px;
                    border-radius:6px;
                    text-decoration:none;
                    font-weight:bold;
                ">
                    Reset Password
                </a>
            </div>

            <p style="font-size:14px;color:#555">
                This link is valid for <b>15 minutes</b> and can be used only once.
            </p>

            <p style="font-size:13px;color:#777">
                If you did not request this reset, please ignore this email.
            </p>

            <hr style="margin:30px 0">

            <p style="font-size:13px;color:#777">
                Anand Pharma Support Team<br>
                Trusted Healthcare
            </p>

        </div>
    </body>
    </html>
    """

    send_html_email(
        to_email=user.email,
        subject="Password Reset Request",
        html_body=email_body
    )

    return {"message": "Password reset link sent to email"}


# ======================================================
# ✅ RESET PASSWORD (TOKEN + NEW PASSWORD)
# ======================================================
@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token == data.token,
                PasswordResetToken.expires_at > datetime.utcnow()
            )
        )
    )
    reset_record = result.scalar_one_or_none()

    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = await db.get(User, reset_record.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🔐 Update password
    user.password = hash_password(data.new_password)

    # 🔥 Token one-time use
    await db.delete(reset_record)
    await db.commit()

    return {"message": "Password reset successful"}


# ======================================================
# ✅ LOGOUT
# ======================================================
@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax"
    )
    return {"message": "Logged out successfully"}


# ======================================================
# ✅ ME
# ======================================================
@router.get("/me", dependencies=[Depends(swagger_security)])
async def me(request: Request):
    user = request.state.user

    return {
        "user_id": user["sub"],
        "role": user["role"]
    }