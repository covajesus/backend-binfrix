from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_customer_access_token
from app.db.session import get_db
from app.models.customer import Customer
from app.services.store_service import StoreService

store_security = HTTPBearer(auto_error=False)


def get_current_store_customer(
    tenant_slug: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(store_security),
    db: Session = Depends(get_db),
) -> Customer:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_customer_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tenant = StoreService(db)._get_public_tenant(tenant_slug)
    if payload["tenant_id"] != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido para esta tienda",
            headers={"WWW-Authenticate": "Bearer"},
        )

    customer = db.get(Customer, payload["customer_id"])
    if customer is None or customer.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cliente no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada",
        )

    return customer


def get_optional_store_customer(
    tenant_slug: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(store_security),
    db: Session = Depends(get_db),
) -> Customer | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None

    payload = decode_customer_access_token(credentials.credentials)
    if payload is None:
        return None

    try:
        tenant = StoreService(db)._get_public_tenant(tenant_slug)
    except Exception:
        return None

    if payload["tenant_id"] != tenant.id:
        return None

    customer = db.get(Customer, payload["customer_id"])
    if customer is None or customer.tenant_id != tenant.id or customer.status != "active":
        return None

    return customer
