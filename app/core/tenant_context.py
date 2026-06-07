from dataclasses import dataclass

from app.models.tenant import Tenant
from app.models.user import User


@dataclass
class TenantContext:
    user: User
    tenant: Tenant
    role: str
