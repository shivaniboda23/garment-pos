from pydantic import BaseModel, EmailStr


# -------------------------
# Register Shop
# -------------------------

class ShopRegisterRequest(BaseModel):
    shop_name: str
    owner_name: str
    phone: str
    email: EmailStr
    password: str


# -------------------------
# Login
# -------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# -------------------------
# JWT Token Response
# -------------------------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# -------------------------
# Current Logged-in User
# -------------------------

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    shop_id: int

    class Config:
        from_attributes = True