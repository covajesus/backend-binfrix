from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.schemas.slider import SliderCreate, SliderOut, SliderUpdate
from app.services.slider_service import SliderService

router = APIRouter(prefix="/sliders", tags=["sliders"])


def _service(ctx: TenantContext, db: Session) -> SliderService:
    return SliderService(db, tenant_id=ctx.tenant.id)


@router.get("", response_model=list[SliderOut])
def list_sliders(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[SliderOut]:
    return _service(ctx, db).list_sliders()


@router.post("", response_model=SliderOut, status_code=status.HTTP_201_CREATED)
def create_slider(
    payload: SliderCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> SliderOut:
    try:
        return _service(ctx, db).create_slider(payload)
    except AppError as exc:
        raise_http(exc)


@router.get("/{slider_id}", response_model=SliderOut)
def get_slider(
    slider_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> SliderOut:
    try:
        return _service(ctx, db).get_slider(slider_id)
    except AppError as exc:
        raise_http(exc)


@router.patch("/{slider_id}", response_model=SliderOut)
def update_slider(
    slider_id: str,
    payload: SliderUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> SliderOut:
    try:
        return _service(ctx, db).update_slider(slider_id, payload)
    except AppError as exc:
        raise_http(exc)


@router.delete("/{slider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_slider(
    slider_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    try:
        _service(ctx, db).delete_slider(slider_id)
    except AppError as exc:
        raise_http(exc)
