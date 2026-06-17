-- Migración incremental: tabla help_pages (multitenant, contenido ayuda storefront)
-- Ejecutar sin borrar datos existentes:
--   python scripts/migrate_help_pages.py
--   mysql -u ... -p binfrix < scripts/migrate_help_pages.sql

USE binfrix;

CREATE TABLE IF NOT EXISTS help_pages (
  id          CHAR(36)      NOT NULL,
  tenant_id   CHAR(36)      NOT NULL,
  slug        VARCHAR(80)   NOT NULL,
  nav_label   VARCHAR(120)  NOT NULL,
  title       VARCHAR(255)  NOT NULL,
  subtitle    VARCHAR(255)  NOT NULL DEFAULT '',
  intro       TEXT          NOT NULL,
  sections    JSON          NOT NULL,
  sort_order  INT           NOT NULL DEFAULT 0,
  status      VARCHAR(20)   NOT NULL DEFAULT 'active',
  created_at  DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at  DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_help_pages_tenant_slug (tenant_id, slug),
  KEY ix_help_pages_tenant_id (tenant_id),
  KEY ix_help_pages_sort_order (sort_order),
  CONSTRAINT fk_help_pages_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
