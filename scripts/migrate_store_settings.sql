-- Migración incremental: tabla store_settings
-- python scripts/migrate_store_settings.py

USE binfrix;

CREATE TABLE IF NOT EXISTS store_settings (
  id            CHAR(36)      NOT NULL,
  tenant_id     CHAR(36)      NOT NULL,
  phone         VARCHAR(40)   NOT NULL DEFAULT '',
  schedule      VARCHAR(120)  NOT NULL DEFAULT '',
  support_label VARCHAR(120)  NOT NULL DEFAULT '',
  support_href  VARCHAR(255)  NOT NULL DEFAULT '/help',
  contact_email VARCHAR(255)  NOT NULL DEFAULT '',
  social_links  JSON          NOT NULL,
  created_at    DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at    DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_store_settings_tenant (tenant_id),
  KEY ix_store_settings_tenant_id (tenant_id),
  CONSTRAINT fk_store_settings_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
