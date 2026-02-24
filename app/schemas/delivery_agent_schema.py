from pydantic import BaseModel, EmailStr, Field, model_validator

class DeliveryAgentCreate(BaseModel):
    full_name: str = Field(min_length=3)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=10)

    password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)

    # ✅ delivery agent extra fields
    vehicle_number: str = Field(min_length=4)
    vehicle_type: str = Field(min_length=3)   # ✅ NEW
    rc_no: str = Field(min_length=5)          # ✅ NEW
    driving_license_no: str = Field(min_length=5)

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Password and Confirm Password do not match")
        return self
