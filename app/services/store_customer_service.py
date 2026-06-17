"""Auth y panel de cuenta para clientes del storefront."""

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.core.security import (
    create_customer_access_token,
    get_password_hash,
    verify_password,
)
from app.models.customer import Customer
from app.models.order import Order
from app.models.payment import Payment
from app.schemas.order import OrderOut
from app.schemas.payment import PaymentOut
from app.schemas.store_auth import (
    CustomerAccountOut,
    CustomerAuthOut,
    CustomerLogin,
    CustomerProfileUpdate,
    CustomerRegister,
    CustomerShippingAddressCreate,
    CustomerShippingAddressOut,
    CustomerShippingAddressUpdate,
)
from app.services.base import BaseService
from app.services.store_service import StoreService
from app.utils.customer_addresses import (
    MAX_SHIPPING_ADDRESSES,
    ensure_single_default,
    normalize_address,
    normalize_addresses,
)
from app.utils.orders import today


class StoreCustomerService(BaseService):
    def _tenant(self, tenant_slug: str):
        return StoreService(self.db)._get_public_tenant(tenant_slug)

    def _serialize_customer(self, customer: Customer) -> CustomerAccountOut:
        addresses = normalize_addresses(customer.shipping_addresses or [])
        return CustomerAccountOut(
            id=customer.id,
            first_name=customer.first_name,
            last_name=customer.last_name,
            email=customer.email,
            phone=customer.phone or "",
            city=customer.city or "",
            shipping_addresses=[CustomerShippingAddressOut(**item) for item in addresses],
        )

    def _save_addresses(self, customer: Customer, addresses: list[dict]) -> list[dict]:
        customer.shipping_addresses = normalize_addresses(addresses)
        self.commit()
        self.db.refresh(customer)
        return customer.shipping_addresses

    def _auth_response(self, customer: Customer, tenant_id: str) -> CustomerAuthOut:
        token = create_customer_access_token(customer.id, customer.email, tenant_id)
        return CustomerAuthOut(
            access_token=token,
            customer=self._serialize_customer(customer),
        )

    def register(self, tenant_slug: str, payload: CustomerRegister) -> CustomerAuthOut:
        tenant = self._tenant(tenant_slug)
        email = payload.email.strip().lower()

        existing = (
            self.db.query(Customer)
            .filter(Customer.tenant_id == tenant.id, Customer.email == email)
            .first()
        )

        if existing is not None and existing.password_hash:
            raise ConflictError("Ya existe una cuenta con este correo")

        password_hash = get_password_hash(payload.password)

        if existing is not None:
            existing.first_name = payload.first_name.strip()
            existing.last_name = payload.last_name.strip()
            existing.phone = payload.phone.strip()
            existing.city = payload.city.strip()
            existing.password_hash = password_hash
            if existing.status != "active":
                existing.status = "active"
            customer = existing
        else:
            customer = Customer(
                tenant_id=tenant.id,
                first_name=payload.first_name.strip(),
                last_name=payload.last_name.strip(),
                email=email,
                phone=payload.phone.strip(),
                city=payload.city.strip(),
                status="active",
                password_hash=password_hash,
                created_at=today(),
            )
            self.db.add(customer)

        self.commit()
        self.db.refresh(customer)
        return self._auth_response(customer, tenant.id)

    def login(self, tenant_slug: str, payload: CustomerLogin) -> CustomerAuthOut:
        tenant = self._tenant(tenant_slug)
        email = payload.email.strip().lower()

        customer = (
            self.db.query(Customer)
            .filter(Customer.tenant_id == tenant.id, Customer.email == email)
            .first()
        )
        if customer is None or not customer.password_hash:
            raise AppError("Correo o contraseña incorrectos", 401)

        if customer.status != "active":
            raise AppError("Cuenta desactivada", 403)

        if not verify_password(payload.password, customer.password_hash):
            raise AppError("Correo o contraseña incorrectos", 401)

        return self._auth_response(customer, tenant.id)

    def get_me(self, customer: Customer) -> CustomerAccountOut:
        return self._serialize_customer(customer)

    def update_profile(
        self,
        customer: Customer,
        payload: CustomerProfileUpdate,
    ) -> CustomerAccountOut:
        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            if value is None:
                continue
            if key in ("first_name", "last_name"):
                setattr(customer, key, value.strip())
            else:
                setattr(customer, key, str(value).strip())
        self.commit()
        self.db.refresh(customer)
        return self._serialize_customer(customer)

    def list_addresses(self, customer: Customer) -> list[CustomerShippingAddressOut]:
        addresses = normalize_addresses(customer.shipping_addresses or [])
        return [CustomerShippingAddressOut(**item) for item in addresses]

    def create_address(
        self,
        customer: Customer,
        payload: CustomerShippingAddressCreate,
    ) -> CustomerAccountOut:
        addresses = normalize_addresses(customer.shipping_addresses or [])
        if len(addresses) >= MAX_SHIPPING_ADDRESSES:
            raise ConflictError(f"Máximo {MAX_SHIPPING_ADDRESSES} direcciones guardadas")

        new_item = normalize_address(
            {
                "id": str(uuid.uuid4()),
                "label": payload.label,
                "address": payload.address,
                "city": payload.city,
                "region": payload.region,
                "phone": payload.phone or customer.phone,
                "is_default": payload.is_default,
            }
        )
        if new_item is None:
            raise AppError("Dirección inválida")

        if not addresses:
            new_item["is_default"] = True
        elif new_item["is_default"]:
            for item in addresses:
                item["is_default"] = False

        addresses.append(new_item)
        self._save_addresses(customer, addresses)
        return self._serialize_customer(customer)

    def update_address(
        self,
        customer: Customer,
        address_id: str,
        payload: CustomerShippingAddressUpdate,
    ) -> CustomerAccountOut:
        addresses = normalize_addresses(customer.shipping_addresses or [])
        index = next((i for i, row in enumerate(addresses) if row["id"] == address_id), None)
        if index is None:
            raise NotFoundError("Dirección no encontrada")

        current = addresses[index]
        data = payload.model_dump(exclude_unset=True)
        merged = {
            **current,
            **{k: v for k, v in data.items() if v is not None},
        }
        if "label" in data and data["label"] is not None:
            merged["label"] = data["label"].strip()
        if "address" in data and data["address"] is not None:
            merged["address"] = data["address"].strip()
        if "city" in data and data["city"] is not None:
            merged["city"] = data["city"].strip()
        if "region" in data and data["region"] is not None:
            merged["region"] = str(data["region"]).strip()
        if "phone" in data and data["phone"] is not None:
            merged["phone"] = str(data["phone"]).strip()

        updated = normalize_address(merged)
        if updated is None:
            raise AppError("Dirección inválida")

        if data.get("is_default"):
            for item in addresses:
                item["is_default"] = False
            updated["is_default"] = True

        addresses[index] = updated
        ensure_single_default(addresses)
        self._save_addresses(customer, addresses)
        return self._serialize_customer(customer)

    def delete_address(self, customer: Customer, address_id: str) -> CustomerAccountOut:
        addresses = normalize_addresses(customer.shipping_addresses or [])
        filtered = [row for row in addresses if row["id"] != address_id]
        if len(filtered) == len(addresses):
            raise NotFoundError("Dirección no encontrada")

        ensure_single_default(filtered)
        self._save_addresses(customer, filtered)
        return self._serialize_customer(customer)

    def set_default_address(self, customer: Customer, address_id: str) -> CustomerAccountOut:
        addresses = normalize_addresses(customer.shipping_addresses or [])
        if not any(row["id"] == address_id for row in addresses):
            raise NotFoundError("Dirección no encontrada")

        ensure_single_default(addresses, default_id=address_id)
        self._save_addresses(customer, addresses)
        return self._serialize_customer(customer)

    def list_orders(self, customer: Customer) -> list[OrderOut]:
        rows = (
            self.db.query(Order)
            .filter(Order.tenant_id == customer.tenant_id, Order.customer_id == customer.id)
            .order_by(Order.created_at.desc())
            .all()
        )
        return [OrderOut.model_validate(row) for row in rows]

    def get_order(self, customer: Customer, order_id: str) -> OrderOut:
        order = (
            self.db.query(Order)
            .filter(
                Order.id == order_id,
                Order.tenant_id == customer.tenant_id,
                Order.customer_id == customer.id,
            )
            .first()
        )
        if order is None:
            raise NotFoundError("Pedido no encontrado")
        return OrderOut.model_validate(order)

    def list_payments(self, customer: Customer) -> list[PaymentOut]:
        rows = (
            self.db.query(Payment)
            .join(Order, Payment.order_id == Order.id)
            .filter(
                Order.tenant_id == customer.tenant_id,
                Order.customer_id == customer.id,
            )
            .order_by(Payment.created_at.desc())
            .all()
        )
        return [PaymentOut.model_validate(row) for row in rows]
