from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(min_length=20)


class SetupStoreRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str | None = Field(default=None, max_length=60)


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


class MeResponse(BaseModel):
    """Authenticated session snapshot used to restore admin SPA state."""

    user: UserOut
    tenants: list[TenantSummary]
    needs_store: bool = False


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: UserOut
    tenants: list[TenantSummary]
    needs_store: bool = False


class SetupStoreResponse(BaseModel):
    tenant: TenantSummary


class MessageResponse(BaseModel):
    message: str
