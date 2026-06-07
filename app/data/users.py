from dataclasses import dataclass

from app.core.security import get_password_hash, verify_password


@dataclass(frozen=True)
class UserRecord:
    id: int
    name: str
    email: str
    role: str
    password_hash: str


DEMO_USERS: list[UserRecord] = [
    UserRecord(
        id=1,
        name="Administrador",
        email="admin@binfrix.com",
        role="admin",
        password_hash=get_password_hash("admin123"),
    ),
]


def get_user_by_email(email: str) -> UserRecord | None:
    normalized = email.strip().lower()
    for user in DEMO_USERS:
        if user.email.lower() == normalized:
            return user
    return None


def authenticate_user(email: str, password: str) -> UserRecord | None:
    user = get_user_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
