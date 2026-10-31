"""Authentication use cases: email register/login, Google sign-in, store provisioning."""

from __future__ import annotations

import secrets
from datetime import date

import httpx
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.core.deps import serialize_user_out
from app.core.exceptions import AppError, ConflictError
from app.core.roles import ROLE_CLIENT_1
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.license import TenantLicense
from app.models.platform_product import PlatformProduct
from app.models.role import Role
from app.models.tenant import Tenant, TenantMembership
from app.models.user import User
from app.schemas.auth import (
    GoogleAuthRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    SetupStoreRequest,
    SetupStoreResponse,
    TenantSummary,
)
from app.schemas.store_settings import StoreSettingsUpdate
from app.services.base import BaseService
from app.services.store_sample_service import StoreSampleService
from app.services.store_settings_service import StoreSettingsService
from app.utils.license_billing import initial_monthly_period
from app.utils.license_plans import PLAN_FULL, PRINCIPAL_MEMBERSHIP_ROLE, max_users_for_plan
from app.utils.slugs import slugify_store_name


class AuthService(BaseService):
    """Owner authentication and first-time tenant store setup."""

    def __init__(self, db: Session):
        super().__init__(db)

    def _client_role(self) -> Role:
        role = self.db.query(Role).filter(Role.slug == ROLE_CLIENT_1).first()
        if role is None:
            raise AppError("Rol de cliente no configurado", 500)
        return role

    def _tenants_for(self, user: User) -> list[TenantSummary]:
        if user.is_superadmin:
            return [
                TenantSummary(id=t.id, name=t.name, slug=t.slug, role="admin")
                for t in self.db.query(Tenant).order_by(Tenant.name).all()
            ]
        memberships = (
            self.db.query(TenantMembership)
            .options(joinedload(TenantMembership.tenant))
            .filter(TenantMembership.user_id == user.id)
            .all()
        )
        return [
            TenantSummary(
                id=m.tenant.id,
                name=m.tenant.name,
                slug=m.tenant.slug,
                role=m.role,
            )
            for m in memberships
            if m.tenant is not None
        ]

    def _login_response(self, user: User) -> LoginResponse:
        user = (
            self.db.query(User)
            .options(joinedload(User.role))
            .filter(User.id == user.id)
            .first()
        )
        tenants = self._tenants_for(user)
        return LoginResponse(
            token=create_access_token(user.id, user.email),
            user=serialize_user_out(user),
            tenants=tenants,
            needs_store=not user.is_superadmin and len(tenants) == 0,
        )

    def login(self, payload: LoginRequest) -> LoginResponse:
        user = (
            self.db.query(User)
            .options(joinedload(User.role))
            .filter(User.email == payload.email.strip().lower())
            .first()
        )
        if user is None or not verify_password(payload.password, user.password_hash):
            raise AppError("Credenciales incorrectas", 401)
        return self._login_response(user)

    def register(self, payload: RegisterRequest) -> LoginResponse:
        email = payload.email.strip().lower()
        if self.db.query(User).filter(User.email == email).first():
            raise ConflictError("Ese correo ya está registrado")

        user = User(
            email=email,
            name=payload.name.strip(),
            password_hash=get_password_hash(payload.password),
            role_id=self._client_role().id,
            is_superadmin=False,
        )
        self.db.add(user)
        self.commit()
        self.db.refresh(user)
        return self._login_response(user)

    def _verify_google_token(self, id_token: str) -> dict:
        settings = get_settings()
        client_id = (settings.google_client_id or "").strip()
        if not client_id:
            raise AppError("Google login no está configurado en el servidor", 503)

        try:
            response = httpx.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token},
                timeout=15.0,
            )
        except httpx.HTTPError as exc:
            raise AppError(f"No se pudo validar Google: {exc}", 502) from exc

        if response.status_code >= 400:
            raise AppError("Token de Google inválido", 401)

        data = response.json()
        if data.get("aud") != client_id:
            raise AppError("Token de Google no corresponde a esta app", 401)
        if data.get("email_verified") not in (True, "true", "1"):
            raise AppError("El correo de Google no está verificado", 401)
        email = (data.get("email") or "").strip().lower()
        if not email:
            raise AppError("Google no devolvió un correo", 401)
        return {
            "email": email,
            "name": (data.get("name") or email.split("@")[0]).strip(),
        }

    def google_login(self, payload: GoogleAuthRequest) -> LoginResponse:
        profile = self._verify_google_token(payload.id_token.strip())
        email = profile["email"]
        user = (
            self.db.query(User)
            .options(joinedload(User.role))
            .filter(User.email == email)
            .first()
        )
        if user is None:
            user = User(
                email=email,
                name=profile["name"],
                password_hash=get_password_hash(secrets.token_urlsafe(32)),
                role_id=self._client_role().id,
                is_superadmin=False,
            )
            self.db.add(user)
            self.commit()
            self.db.refresh(user)
        return self._login_response(user)

    def _unique_slug(self, base: str) -> str:
        slug = slugify_store_name(base)
        candidate = slug
        index = 2
        while self.db.query(Tenant).filter(Tenant.slug == candidate).first():
            suffix = f"-{index}"
            candidate = f"{slug[: 48 - len(suffix)]}{suffix}"
            index += 1
        return candidate

    def setup_store(self, user: User, payload: SetupStoreRequest) -> SetupStoreResponse:
        if user.is_superadmin:
            raise AppError("Los administradores de plataforma no crean tienda aquí", 400)

        existing = (
            self.db.query(TenantMembership)
            .filter(TenantMembership.user_id == user.id)
            .first()
        )
        if existing:
            tenant = self.db.get(Tenant, existing.tenant_id)
            return SetupStoreResponse(
                tenant=TenantSummary(
                    id=tenant.id,
                    name=tenant.name,
                    slug=tenant.slug,
                    role=existing.role,
                )
            )

        name = payload.name.strip()
        if len(name) < 2:
            raise AppError("El nombre de la tienda es muy corto", 400)

        requested = (payload.slug or "").strip()
        slug = self._unique_slug(requested or name)

        product = self.db.get(PlatformProduct, "ecommerce-b2c")
        if product is None:
            raise AppError("Producto ecommerce-b2c no configurado", 500)

        tenant = Tenant(name=name, slug=slug, status="active")
        self.db.add(tenant)
        self.db.flush()

        self.db.add(
            TenantMembership(
                tenant_id=tenant.id,
                user_id=user.id,
                role=PRINCIPAL_MEMBERSHIP_ROLE,
            )
        )
        starts_at, ends_at = initial_monthly_period(date.today())
        self.db.add(
            TenantLicense(
                tenant_id=tenant.id,
                platform_product_id="ecommerce-b2c",
                status="active",
                plan=PLAN_FULL,
                starts_at=starts_at,
                ends_at=ends_at,
                max_users=max_users_for_plan(PLAN_FULL),
            )
        )
        self.db.flush()

        store_url = f"https://{slug}.binfrix.io"
        settings = StoreSettingsService(self.db, tenant_id=tenant.id)
        settings.get_or_create(tenant.id)
        settings.update_settings(StoreSettingsUpdate(store_url=store_url))
        StoreSampleService(self.db).seed_new_store(
            tenant.id,
            store_name=name,
            store_url=store_url,
        )

        self.commit()
        self.db.refresh(tenant)

        return SetupStoreResponse(
            tenant=TenantSummary(
                id=tenant.id,
                name=tenant.name,
                slug=tenant.slug,
                role=PRINCIPAL_MEMBERSHIP_ROLE,
            )
        )
