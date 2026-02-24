from pydantic import BaseModel, EmailStr


class UserProfileResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str | None = None
    role: str

    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None

    is_verified: bool
    is_active: bool

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
