from datetime import date

from pydantic import BaseModel, EmailStr


class PlatformUserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    role_name: str = ""
    status: str = "active"
    created_at: date | None = None

    model_config = {"from_attributes": True}


class PlatformUserRoleUpdate(BaseModel):
    role: str
