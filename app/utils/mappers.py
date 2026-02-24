from models.user import User


def map_delivery_agent(user: User) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "is_online": user.is_online,
        "street": user.da_street,
        "city": user.da_city,
        "state": user.da_state,
        "pincode": user.da_pincode,
    }
