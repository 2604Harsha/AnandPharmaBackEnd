from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator

from api.routers.routes.delivery_agent_profile import IndianState

class UserCreate(BaseModel):
    full_name: str = Field(min_length=3)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=10)
    password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)
    role: str = Field(default="user")
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None

@model_validator(mode="after")
def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Password and Confirm Password do not match")
        return self

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)

class UserResponse(BaseModel):
    id: int
    full_name: str | None
    email: str
    phone: str | None
    role: str
    pharmacy_name: str | None
    shop_no: str | None
    store_street: str | None
    store_city: str | None
    store_state: str | None
    is_active: bool
    is_verified: bool
    is_online: bool
   

class UserListResponse(BaseModel):
    count: int
    users: list[UserResponse]

class Response(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    role: str

    # ✅ USER ADDRESS FIELDS
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]

    is_active: bool
    is_verified: bool
    is_online: bool

class ListResponse(BaseModel):
    count: int
    users: list[Response]

class DeliveryAddressRequest(BaseModel):
    street: str = Field(..., example="MG Road")
    city: str = Field(..., example="Hyderabad")
    state: IndianState
    pincode: str = Field(..., min_length=6, max_length=6)

class DeliveryAgentResponse(BaseModel):
    id: int
    full_name: str | None
    email: str
    phone: str | None
    role: str
    street: str | None
    city: str | None
    state: str | None
    pincode: str | None
    is_active: bool
    is_verified: bool
    is_online: bool
   

class DeliveryAgentListResponse(BaseModel):
    count: int
    users: list[DeliveryAgentResponse]


class DeliveryAgentUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

    vehicle_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    rc_no: Optional[str] = None
    driving_license_no: Optional[str] = None

    
@model_validator(mode="after")
def check_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("New password and confirm password do not match")
        return self

model_config = {"from_attributes": True}

