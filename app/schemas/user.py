from pydantic import BaseModel, EmailStr, Field, model_validator

class UserCreate(BaseModel):
    full_name: str = Field(min_length=3)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=10)
    password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)
    role: str = Field(default="user")

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
@model_validator(mode="after")
def check_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("New password and confirm password do not match")
        return self

model_config = {"from_attributes": True}
