from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.deps import get_tenant_context
from app.core.exceptions import AppError, raise_http
from app.core.tenant_context import TenantContext
from app.db.session import get_db
from app.schemas.custom_storefront_template import CustomStorefrontTemplateOut
from app.services.custom_storefront_template_service import CustomStorefrontTemplateService

router = APIRouter(prefix="/storefront-templates", tags=["storefront-templates"])


def _service(ctx: TenantContext, db: Session) -> CustomStorefrontTemplateService:
    return CustomStorefrontTemplateService(db, tenant_id=ctx.tenant.id)


@router.get("", response_model=list[CustomStorefrontTemplateOut])
def list_storefront_templates(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[CustomStorefrontTemplateOut]:
    return _service(ctx, db).list_templates()


@router.post("/upload", response_model=CustomStorefrontTemplateOut, status_code=status.HTTP_201_CREATED)
async def upload_storefront_template(
    file: UploadFile = File(...),
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> CustomStorefrontTemplateOut:
    try:
        content = await file.read()
        return _service(ctx, db).upload_package(content)
    except AppError as exc:
        raise_http(exc)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_storefront_template(
    template_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    try:
        _service(ctx, db).delete_template(template_id)
    except AppError as exc:
        raise_http(exc)
