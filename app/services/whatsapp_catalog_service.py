"""WhatsApp Commerce catalog integration (Meta).

Stores Meta credentials on store settings. Product sync against the Catalog API
will use these fields when enabled and ready.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.store_settings import StoreSettings
from app.services.base import BaseService
from app.services.store_settings_service import StoreSettingsService, _whatsapp_catalog_ready


class WhatsAppCatalogService(BaseService):
    """Reads catalog readiness for a tenant; sync hooks land here later."""

    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db)
        self.tenant_id = tenant_id

    def is_ready(self) -> bool:
        row = (
            self.db.query(StoreSettings)
            .filter(StoreSettings.tenant_id == self.tenant_id)
            .first()
        )
        if row is None:
            return False
        return _whatsapp_catalog_ready(row)

    def get_admin_status(self) -> dict:
        settings = StoreSettingsService(self.db, self.tenant_id).get_settings()
        return {
            "enabled": settings.whatsapp_catalog_enabled,
            "ready": settings.whatsapp_catalog_ready,
            "waba_id": settings.whatsapp_waba_id,
            "phone_number_id": settings.whatsapp_phone_number_id,
            "catalog_id": settings.whatsapp_catalog_id,
            "access_token_configured": settings.whatsapp_meta_access_token_configured,
        }
