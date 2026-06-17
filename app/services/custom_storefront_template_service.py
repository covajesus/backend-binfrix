from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.custom_storefront_template import CustomStorefrontTemplate
from app.models.store_settings import StoreSettings
from app.schemas.custom_storefront_template import (
    CustomStorefrontTemplateOut,
    CustomStorefrontTemplatePublicOut,
)
from app.schemas.store_settings import ALLOWED_STOREFRONT_TEMPLATES
from app.services.base import BaseService
from app.utils.template_package import ParsedTemplatePackage, parse_template_zip


def _to_out(row: CustomStorefrontTemplate) -> CustomStorefrontTemplateOut:
    return CustomStorefrontTemplateOut(
        id=row.id,
        slug=row.slug,
        template_id=row.template_id,
        name=row.name,
        description=row.description,
        extends_template=row.extends_template,
        theme_colors=row.theme_colors or {},
        has_custom_css=bool((row.custom_css or "").strip()),
        preview_image=row.preview_image or "",
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _to_public_out(row: CustomStorefrontTemplate) -> CustomStorefrontTemplatePublicOut:
    return CustomStorefrontTemplatePublicOut(
        template_id=row.template_id,
        slug=row.slug,
        name=row.name,
        description=row.description,
        extends_template=row.extends_template,
        theme_colors=row.theme_colors or {},
        has_custom_css=bool((row.custom_css or "").strip()),
        preview_image=row.preview_image or "",
    )


class CustomStorefrontTemplateService(BaseService):
    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db)
        self.tenant_id = tenant_id

    def list_templates(self) -> list[CustomStorefrontTemplateOut]:
        rows = (
            self.db.query(CustomStorefrontTemplate)
            .filter(CustomStorefrontTemplate.tenant_id == self.tenant_id)
            .order_by(CustomStorefrontTemplate.name)
            .all()
        )
        return [_to_out(row) for row in rows]

    def list_public_templates(self) -> list[CustomStorefrontTemplatePublicOut]:
        rows = (
            self.db.query(CustomStorefrontTemplate)
            .filter(
                CustomStorefrontTemplate.tenant_id == self.tenant_id,
                CustomStorefrontTemplate.status == "active",
            )
            .order_by(CustomStorefrontTemplate.name)
            .all()
        )
        return [_to_public_out(row) for row in rows]

    def get_by_template_id(self, template_id: str) -> CustomStorefrontTemplate | None:
        if not template_id.startswith("custom-"):
            return None
        slug = template_id[7:]
        return (
            self.db.query(CustomStorefrontTemplate)
            .filter(
                CustomStorefrontTemplate.tenant_id == self.tenant_id,
                CustomStorefrontTemplate.slug == slug,
                CustomStorefrontTemplate.status == "active",
            )
            .first()
        )

    def get_css(self, template_id: str) -> str:
        row = self.get_by_template_id(template_id)
        if row is None:
            raise NotFoundError("Plantilla no encontrada")
        return row.custom_css or ""

    def upload_package(self, file_bytes: bytes) -> CustomStorefrontTemplateOut:
        parsed = parse_template_zip(file_bytes)
        return self._upsert_parsed(parsed)

    def _upsert_parsed(self, parsed: ParsedTemplatePackage) -> CustomStorefrontTemplateOut:
        row = (
            self.db.query(CustomStorefrontTemplate)
            .filter(
                CustomStorefrontTemplate.tenant_id == self.tenant_id,
                CustomStorefrontTemplate.slug == parsed.slug,
            )
            .first()
        )
        if row is None:
            row = CustomStorefrontTemplate(tenant_id=self.tenant_id, slug=parsed.slug)
            self.db.add(row)

        row.name = parsed.name
        row.description = parsed.description
        row.extends_template = parsed.extends_template
        row.theme_colors = parsed.theme_colors
        row.custom_css = parsed.custom_css
        if parsed.preview_image:
            row.preview_image = parsed.preview_image
        row.status = "active"

        self.commit()
        self.db.refresh(row)
        return _to_out(row)

    def delete_template(self, template_id: str) -> None:
        if not template_id.startswith("custom-"):
            raise ConflictError("Solo se pueden eliminar plantillas personalizadas")
        slug = template_id[7:]
        row = (
            self.db.query(CustomStorefrontTemplate)
            .filter(
                CustomStorefrontTemplate.tenant_id == self.tenant_id,
                CustomStorefrontTemplate.slug == slug,
            )
            .first()
        )
        if row is None:
            raise NotFoundError("Plantilla no encontrada")

        settings = (
            self.db.query(StoreSettings)
            .filter(StoreSettings.tenant_id == self.tenant_id)
            .first()
        )
        if settings and settings.storefront_template == row.template_id:
            settings.storefront_template = row.extends_template or "sports"
            if settings.storefront_template not in ALLOWED_STOREFRONT_TEMPLATES:
                settings.storefront_template = "sports"

        self.db.delete(row)
        self.commit()

    @staticmethod
    def is_allowed_template_id(
        db: Session,
        tenant_id: str,
        template_id: str,
    ) -> bool:
        if template_id in ALLOWED_STOREFRONT_TEMPLATES:
            return True
        if not template_id.startswith("custom-"):
            return False
        slug = template_id[7:]
        row = (
            db.query(CustomStorefrontTemplate)
            .filter(
                CustomStorefrontTemplate.tenant_id == tenant_id,
                CustomStorefrontTemplate.slug == slug,
                CustomStorefrontTemplate.status == "active",
            )
            .first()
        )
        return row is not None
