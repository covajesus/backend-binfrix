from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(user_id: str, email: str, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
    if payload.get("type") == "customer":
        return None
    user_id = payload.get("sub")
    email = payload.get("email")
    if not isinstance(user_id, str) or not isinstance(email, str):
        return None
    return {"user_id": user_id, "email": email}


def create_customer_access_token(
    customer_id: str,
    email: str,
    tenant_id: str,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {
        "sub": customer_id,
        "email": email,
        "tenant_id": tenant_id,
        "type": "customer",
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_customer_access_token(token: str) -> dict | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
    if payload.get("type") != "customer":
        return None
    customer_id = payload.get("sub")
    email = payload.get("email")
    tenant_id = payload.get("tenant_id")
    if (
        not isinstance(customer_id, str)
        or not isinstance(email, str)
        or not isinstance(tenant_id, str)
    ):
        return None
    return {
        "customer_id": customer_id,
        "email": email,
        "tenant_id": tenant_id,
    }
