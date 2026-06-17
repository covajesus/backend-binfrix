from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import PlainTextResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, raise_http
from app.core.store_deps import get_current_store_customer, get_optional_store_customer
from app.db.session import get_db
from app.models.customer import Customer
from app.models.tenant import Tenant
from app.schemas.catalog import CatalogProductOut
from app.schemas.category import CategoryOut
from app.schemas.help_page import HelpPageOut
from app.schemas.order import OrderCreate, OrderOut
from app.schemas.payment_session import PaymentSessionInitIn, PaymentSessionInitOut
from app.schemas.slider import StoreSliderOut
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
from app.schemas.store_settings import StoreSettingsPublicOut
from app.schemas.custom_storefront_template import CustomStorefrontTemplatePublicOut
from app.schemas.payment import PaymentOut
from app.services.custom_storefront_template_service import CustomStorefrontTemplateService
from app.services.payment_gateway_service import PaymentGatewayService
from app.services.store_customer_service import StoreCustomerService
from app.services.store_service import StoreService

router = APIRouter(prefix="/store", tags=["store"])


def _service(db: Session) -> StoreService:
    return StoreService(db)


def _customer_service(db: Session) -> StoreCustomerService:
    return StoreCustomerService(db)


def _payment_gateway_service(db: Session) -> PaymentGatewayService:
    return PaymentGatewayService(db)


def _tenant_id_for_slug(db: Session, tenant_slug: str) -> str:
    tenant = (
        db.query(Tenant)
        .filter(Tenant.slug == tenant_slug, Tenant.status == "active")
        .first()
    )
    if tenant is None:
        raise AppError("Tienda no encontrada", 404)
    return tenant.id


@router.get("/by-id/{tenant_id}/info")
def store_info_by_id(tenant_id: str, db: Session = Depends(get_db)) -> dict:
    try:
        return _service(db).get_store_info_by_id(tenant_id)
    except AppError as exc:
        raise_http(exc)


@router.get("/{tenant_slug}/info")
def store_info(tenant_slug: str, db: Session = Depends(get_db)) -> dict:
    try:
        return _service(db).get_store_info(tenant_slug)
    except AppError as exc:
        raise_http(exc)


@router.get("/{tenant_slug}/settings", response_model=StoreSettingsPublicOut)
def store_settings(tenant_slug: str, db: Session = Depends(get_db)) -> StoreSettingsPublicOut:
    try:
        return _service(db).get_store_settings(tenant_slug)
    except AppError as exc:
        raise_http(exc)


@router.get(
    "/{tenant_slug}/storefront-templates",
    response_model=list[CustomStorefrontTemplatePublicOut],
)
def store_custom_templates(
    tenant_slug: str,
    db: Session = Depends(get_db),
) -> list[CustomStorefrontTemplatePublicOut]:
    try:
        tenant_id = _tenant_id_for_slug(db, tenant_slug)
        return CustomStorefrontTemplateService(db, tenant_id).list_public_templates()
    except AppError as exc:
        raise_http(exc)


@router.get("/{tenant_slug}/storefront-templates/{template_id}/styles.css")
def store_custom_template_css(
    tenant_slug: str,
    template_id: str,
    db: Session = Depends(get_db),
) -> PlainTextResponse:
    try:
        tenant_id = _tenant_id_for_slug(db, tenant_slug)
        css = CustomStorefrontTemplateService(db, tenant_id).get_css(template_id)
        return PlainTextResponse(css, media_type="text/css")
    except AppError as exc:
        raise_http(exc)


@router.get("/{tenant_slug}/categories", response_model=list[CategoryOut])
def store_categories(tenant_slug: str, db: Session = Depends(get_db)) -> list[CategoryOut]:
    try:
        return _service(db).list_categories(tenant_slug)
    except AppError as exc:
        raise_http(exc)


@router.get("/{tenant_slug}/sliders", response_model=list[StoreSliderOut])
def store_sliders(tenant_slug: str, db: Session = Depends(get_db)) -> list[StoreSliderOut]:
    try:
        return _service(db).list_sliders(tenant_slug)
    except AppError as exc:
        raise_http(exc)


@router.get("/{tenant_slug}/help", response_model=list[HelpPageOut])
def store_help_pages(tenant_slug: str, db: Session = Depends(get_db)) -> list[HelpPageOut]:
    try:
        return _service(db).list_help_pages(tenant_slug)
    except AppError as exc:
        raise_http(exc)


@router.get("/{tenant_slug}/help/{page_slug}", response_model=HelpPageOut)
def store_help_page(
    tenant_slug: str,
    page_slug: str,
    db: Session = Depends(get_db),
) -> HelpPageOut:
    try:
        return _service(db).get_help_page(tenant_slug, page_slug)
    except AppError as exc:
        raise_http(exc)


@router.get("/{tenant_slug}/catalog", response_model=list[CatalogProductOut])
def store_catalog(tenant_slug: str, db: Session = Depends(get_db)) -> list[CatalogProductOut]:
    try:
        return _service(db).list_catalog(tenant_slug)
    except AppError as exc:
        raise_http(exc)


@router.get("/{tenant_slug}/catalog/{item_id}", response_model=CatalogProductOut)
def store_catalog_item(
    tenant_slug: str,
    item_id: str,
    db: Session = Depends(get_db),
) -> CatalogProductOut:
    try:
        return _service(db).get_catalog_item(tenant_slug, item_id)
    except AppError as exc:
        raise_http(exc)


@router.post("/{tenant_slug}/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def store_create_order(
    tenant_slug: str,
    payload: OrderCreate,
    db: Session = Depends(get_db),
    customer: Customer | None = Depends(get_optional_store_customer),
) -> OrderOut:
    try:
        return _service(db).create_order(tenant_slug, payload, customer)
    except AppError as exc:
        raise_http(exc)


@router.post(
    "/{tenant_slug}/payments/session",
    response_model=PaymentSessionInitOut,
)
def store_init_payment_session(
    tenant_slug: str,
    payload: PaymentSessionInitIn,
    db: Session = Depends(get_db),
) -> PaymentSessionInitOut:
    try:
        tenant_id = _tenant_id_for_slug(db, tenant_slug)
        return _payment_gateway_service(db).init_session(
            tenant_slug,
            tenant_id,
            payload.order_id,
        )
    except AppError as exc:
        raise_http(exc)


@router.post("/{tenant_slug}/payments/return")
def store_payment_return(
    tenant_slug: str,
    token_ws: str = Form(default=""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    try:
        tenant_id = _tenant_id_for_slug(db, tenant_slug)
        redirect_url = _payment_gateway_service(db).complete_session(tenant_id, token_ws)
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    except AppError as exc:
        raise_http(exc)


@router.post("/{tenant_slug}/auth/register", response_model=CustomerAuthOut, status_code=status.HTTP_201_CREATED)
def store_register(
    tenant_slug: str,
    payload: CustomerRegister,
    db: Session = Depends(get_db),
) -> CustomerAuthOut:
    try:
        return _customer_service(db).register(tenant_slug, payload)
    except AppError as exc:
        raise_http(exc)


@router.post("/{tenant_slug}/auth/login", response_model=CustomerAuthOut)
def store_login(
    tenant_slug: str,
    payload: CustomerLogin,
    db: Session = Depends(get_db),
) -> CustomerAuthOut:
    try:
        return _customer_service(db).login(tenant_slug, payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/{tenant_slug}/auth/me", response_model=CustomerAccountOut)
def store_me(
    tenant_slug: str,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_store_customer),
) -> CustomerAccountOut:
    try:
        return _customer_service(db).get_me(customer)
    except AppError as exc:
        raise_http(exc)


@router.patch("/{tenant_slug}/account/profile", response_model=CustomerAccountOut)
def store_update_profile(
    tenant_slug: str,
    payload: CustomerProfileUpdate,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_store_customer),
) -> CustomerAccountOut:
    try:
        return _customer_service(db).update_profile(customer, payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/{tenant_slug}/account/orders", response_model=list[OrderOut])
def store_account_orders(
    tenant_slug: str,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_store_customer),
) -> list[OrderOut]:
    try:
        return _customer_service(db).list_orders(customer)
    except AppError as exc:
        raise_http(exc)


@router.get("/{tenant_slug}/account/orders/{order_id}", response_model=OrderOut)
def store_account_order(
    tenant_slug: str,
    order_id: str,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_store_customer),
) -> OrderOut:
    try:
        return _customer_service(db).get_order(customer, order_id)
    except AppError as exc:
        raise_http(exc)


@router.get("/{tenant_slug}/account/payments", response_model=list[PaymentOut])
def store_account_payments(
    tenant_slug: str,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_store_customer),
) -> list[PaymentOut]:
    try:
        return _customer_service(db).list_payments(customer)
    except AppError as exc:
        raise_http(exc)


@router.get(
    "/{tenant_slug}/account/addresses",
    response_model=list[CustomerShippingAddressOut],
)
def store_account_addresses(
    tenant_slug: str,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_store_customer),
) -> list[CustomerShippingAddressOut]:
    try:
        return _customer_service(db).list_addresses(customer)
    except AppError as exc:
        raise_http(exc)


@router.post(
    "/{tenant_slug}/account/addresses",
    response_model=CustomerAccountOut,
    status_code=status.HTTP_201_CREATED,
)
def store_create_address(
    tenant_slug: str,
    payload: CustomerShippingAddressCreate,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_store_customer),
) -> CustomerAccountOut:
    try:
        return _customer_service(db).create_address(customer, payload)
    except AppError as exc:
        raise_http(exc)


@router.patch(
    "/{tenant_slug}/account/addresses/{address_id}",
    response_model=CustomerAccountOut,
)
def store_update_address(
    tenant_slug: str,
    address_id: str,
    payload: CustomerShippingAddressUpdate,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_store_customer),
) -> CustomerAccountOut:
    try:
        return _customer_service(db).update_address(customer, address_id, payload)
    except AppError as exc:
        raise_http(exc)


@router.delete(
    "/{tenant_slug}/account/addresses/{address_id}",
    response_model=CustomerAccountOut,
)
def store_delete_address(
    tenant_slug: str,
    address_id: str,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_store_customer),
) -> CustomerAccountOut:
    try:
        return _customer_service(db).delete_address(customer, address_id)
    except AppError as exc:
        raise_http(exc)


@router.post(
    "/{tenant_slug}/account/addresses/{address_id}/default",
    response_model=CustomerAccountOut,
)
def store_set_default_address(
    tenant_slug: str,
    address_id: str,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_store_customer),
) -> CustomerAccountOut:
    try:
        return _customer_service(db).set_default_address(customer, address_id)
    except AppError as exc:
        raise_http(exc)
