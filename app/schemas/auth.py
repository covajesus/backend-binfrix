from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    role_name: str = ""
    is_superadmin: bool = False

    model_config = {"from_attributes": True}


class RoleOut(BaseModel):
    id: str
    slug: str
    name: str
    description: str

    model_config = {"from_attributes": True}


class TenantSummary(BaseModel):
    id: str
    name: str
    slug: str
    role: str

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: UserOut
    tenants: list[TenantSummary]


class MessageResponse(BaseModel):
    message: str
