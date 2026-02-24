from datetime import datetime
from fastapi import APIRouter, Depends, Response, HTTPException, Request, status
from fastapi import security
from fastapi.security import HTTPBasicCredentials, HTTPBearer
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.delivery_agent_schema import DeliveryAgentCreate
from schemas.pharmacist_schema import PharmacistCreate
from models.password_reset import PasswordResetToken
from core.security import hash_password
from models.user import User
from models.email_otp import EmailOTP
from services.email_service import send_html_email
from services.email_service import send_auth_otp_email, resend_auth_otp_email
from utils.otp import generate_otp
from schemas.user import DeliveryAgentUpdate, ResetPasswordRequest, UserCreate, UserLogin
from services.auth_service import create_delivery_agent, create_pharmacist, create_user, authenticate_user, update_delivery_agent
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

    # ✅ Send email
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
    # 🔍 find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🔍 verify OTP
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

    # ⭐⭐⭐ MAIN FIX — ACTIVATE USER
    user.is_verified = True
    user.is_active = True

    # 🔥 delete used OTP
    await db.delete(record)

    await db.commit()
    await db.refresh(user)

    return {
        "message": "Email verified successfully",
        "status": "ACTIVE",
        "user_id": user.id,
        "role": user.role
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

@router.post("/create")
async def create_pharmacist_account(
    user: PharmacistCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("ADMIN"))
):
    # ✅ Create Pharmacist
    new_user = await create_pharmacist(db, user)

    # ✅ Generate OTP
    otp = generate_otp()
    db.add(
        EmailOTP(
            user_id=new_user.id,
            otp=otp,
            expires_at=EmailOTP.expiry_time()
        )
    )
    await db.commit()

    # ✅ Send OTP Email
    send_auth_otp_email(
        email=new_user.email,
        name=new_user.full_name,
        otp=otp
    )

    return {
        "message": "Pharmacist account created successfully",
        "status": "NOT VERIFIED",
        "role": "pharmacist",
        "license_no": new_user.license_no,
        "shop_no": new_user.shop_no
    }

@router.delete("/delete/{pharmacist_id}")
async def delete_pharmacist_account(
    pharmacist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("ADMIN"))
):
    # 🔍 Find pharmacist
    result = await db.execute(
        select(User).where(
            User.id == pharmacist_id,
            User.role == "pharmacist"
        )
    )
    pharmacist = result.scalar_one_or_none()

    if not pharmacist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pharmacist not found"
        )

    # ✅ STEP 1: Delete OTPs first (VERY IMPORTANT)
    await db.execute(
        delete(EmailOTP).where(EmailOTP.user_id == pharmacist_id)
    )

    # ✅ STEP 2: Delete user
    await db.delete(pharmacist)

    await db.commit()

    return {
        "message": "Pharmacist deleted successfully",
        "pharmacist_id": pharmacist_id
    }

@router.post("/create-Delivery")
async def create_delivery_agent_account(
    user: DeliveryAgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("ADMIN"))
):
    new_user = await create_delivery_agent(db, user)

    otp = generate_otp()
    db.add(
        EmailOTP(
            user_id=new_user.id,
            otp=otp,
            expires_at=EmailOTP.expiry_time()
        )
    )
    await db.commit()

    send_auth_otp_email(
        email=new_user.email,
        name=new_user.full_name,
        otp=otp
    )

    return {
        "message": "Delivery agent account created successfully",
        "status": "NOT VERIFIED",
        "role": "delivery_agent",
        "vehicle_number": new_user.vehicle_number,
        "vehicle_type": new_user.vehicle_type,  # ✅ NEW
        "rc_no": new_user.rc_no                 # ✅ NEW
    }

@router.put("/update-delivery/{user_id}")
async def update_delivery_agent_account(
    user_id: int,
    user_data: DeliveryAgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("delivery_agent"))
):
    updated_user = await update_delivery_agent(db, user_id, user_data)

    return {
        "message": "Delivery agent updated successfully",
        "id": updated_user.id,
        "full_name": updated_user.full_name,
        "email": updated_user.email,
        "phone": updated_user.phone,
        "vehicle_number": updated_user.vehicle_number,
        "vehicle_type": updated_user.vehicle_type,
        "rc_no": updated_user.rc_no,
        "driving_license_no": updated_user.driving_license_no
    }


@router.delete("/delete-delivery/{user_id}")
async def delete_delivery_agent_account(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("ADMIN"))
):
    # 🔹 check user
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.role == "delivery_agent"
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Delivery agent not found")

    # ✅ STEP 1: delete OTPs first (VERY IMPORTANT)
    await db.execute(
        delete(EmailOTP).where(EmailOTP.user_id == user_id)
    )

    # ✅ STEP 2: now delete user
    await db.delete(user)

    # ✅ STEP 3: commit once
    await db.commit()

    return {"message": "Delivery agent deleted successfully"}



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