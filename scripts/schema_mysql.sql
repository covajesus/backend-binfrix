-- =============================================================================
-- Binfrix — Esquema completo MySQL
-- Ejecutar en MySQL 8.0+ o MariaDB 10.5+
-- =============================================================================

CREATE DATABASE IF NOT EXISTS binfrix
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE binfrix;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS support_tickets;
DROP TABLE IF EXISTS catalog_products;
DROP TABLE IF EXISTS help_pages;
DROP TABLE IF EXISTS store_settings;
DROP TABLE IF EXISTS sliders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS tenant_licenses;
DROP TABLE IF EXISTS tenant_memberships;
DROP TABLE IF EXISTS platform_products;
DROP TABLE IF EXISTS tenants;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;

SET FOREIGN_KEY_CHECKS = 1;

-- -----------------------------------------------------------------------------
-- Roles de plataforma (Administrador, Cliente tipo 1, Cliente tipo 2)
-- -----------------------------------------------------------------------------
CREATE TABLE roles (
  id          CHAR(36)     NOT NULL,
  slug        VARCHAR(50)  NOT NULL,
  name        VARCHAR(100) NOT NULL,
  description TEXT         NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_roles_slug (slug),
  KEY ix_roles_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- Usuarios del sistema (admin / staff)
-- -----------------------------------------------------------------------------
CREATE TABLE users (
  id            CHAR(36)      NOT NULL,
  email         VARCHAR(255)  NOT NULL,
  password_hash VARCHAR(255)  NOT NULL,
  name          VARCHAR(255)  NOT NULL,
  role_id       CHAR(36)      NULL,
  is_superadmin TINYINT(1)    NOT NULL DEFAULT 0,
  created_at    DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email),
  KEY ix_users_email (email),
  KEY ix_users_role_id (role_id),
  CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- Tenants (empresas / tiendas multi-tenant)
-- -----------------------------------------------------------------------------
CREATE TABLE tenants (
  id         CHAR(36)     NOT NULL,
  name       VARCHAR(255) NOT NULL,
  slug       VARCHAR(100) NOT NULL,
  status     VARCHAR(20)  NOT NULL DEFAULT 'active',
  created_at DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_tenants_slug (slug),
  KEY ix_tenants_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- Productos SaaS Binfrix (módulos: ecommerce-b2c, pagos, autolavado, etc.)
-- -----------------------------------------------------------------------------
CREATE TABLE platform_products (
  id          VARCHAR(50)  NOT NULL,
  name        VARCHAR(255) NOT NULL,
  description TEXT         NOT NULL,
  is_active   TINYINT(1)   NOT NULL DEFAULT 1,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- Membresía usuario ↔ tenant
-- -----------------------------------------------------------------------------
CREATE TABLE tenant_memberships (
  id         CHAR(36)    NOT NULL,
  tenant_id  CHAR(36)    NOT NULL,
  user_id    CHAR(36)    NOT NULL,
  role       VARCHAR(30) NOT NULL DEFAULT 'admin',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_tenant_user (tenant_id, user_id),
  KEY ix_tenant_memberships_tenant_id (tenant_id),
  KEY ix_tenant_memberships_user_id (user_id),
  CONSTRAINT fk_memberships_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id),
  CONSTRAINT fk_memberships_user   FOREIGN KEY (user_id)   REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- Licencias de productos Binfrix por tenant
-- -----------------------------------------------------------------------------
CREATE TABLE tenant_licenses (
  id                  CHAR(36)    NOT NULL,
  tenant_id           CHAR(36)    NOT NULL,
  platform_product_id VARCHAR(50) NOT NULL,
  status              VARCHAR(20) NOT NULL DEFAULT 'active',
  plan                VARCHAR(50) NOT NULL DEFAULT 'standard',
  starts_at           DATE        NULL,
  ends_at             DATE        NULL,
  max_users           INT         NULL,
  created_at          DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY ix_tenant_licenses_tenant_id (tenant_id),
  KEY ix_tenant_licenses_platform_product_id (platform_product_id),
  CONSTRAINT fk_licenses_tenant  FOREIGN KEY (tenant_id)           REFERENCES tenants (id),
  CONSTRAINT fk_licenses_product FOREIGN KEY (platform_product_id) REFERENCES platform_products (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- Categorías del catálogo ecommerce (por tenant)
-- -----------------------------------------------------------------------------
CREATE TABLE categories (
  id          CHAR(36)     NOT NULL,
  tenant_id   CHAR(36)     NOT NULL,
  name        VARCHAR(255) NOT NULL,
  description TEXT         NOT NULL,
  image_url   TEXT         NOT NULL,
  status      VARCHAR(20)  NOT NULL DEFAULT 'active',
  created_at  DATE         NOT NULL,
  PRIMARY KEY (id),
  KEY ix_categories_tenant_id (tenant_id),
  CONSTRAINT fk_categories_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- Clientes (por tenant)
-- -----------------------------------------------------------------------------
CREATE TABLE customers (
  id          CHAR(36)     NOT NULL,
  tenant_id   CHAR(36)     NOT NULL,
  first_name  VARCHAR(120) NOT NULL,
  last_name   VARCHAR(120) NOT NULL,
  email       VARCHAR(255) NOT NULL,
  phone       VARCHAR(50)  NOT NULL DEFAULT '',
  city        VARCHAR(120) NOT NULL DEFAULT '',
  status      VARCHAR(20)  NOT NULL DEFAULT 'active',
  notes       TEXT         NOT NULL,
  created_at  DATE         NOT NULL,
  PRIMARY KEY (id),
  KEY ix_customers_tenant_id (tenant_id),
  KEY ix_customers_email (email),
  CONSTRAINT fk_customers_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- Sliders / banners del home (por tenant)
-- -----------------------------------------------------------------------------
CREATE TABLE sliders (
  id           CHAR(36)      NOT NULL,
  tenant_id    CHAR(36)      NOT NULL,
  title        VARCHAR(255)  NOT NULL,
  subtitle     VARCHAR(255)  NOT NULL DEFAULT '',
  cta          VARCHAR(120)  NOT NULL DEFAULT 'Comprar',
  link_suffix  VARCHAR(255)  NOT NULL DEFAULT '',
  image_url    TEXT          NOT NULL,
  theme        VARCHAR(10)   NOT NULL DEFAULT 'dark',
  sort_order   INT           NOT NULL DEFAULT 0,
  status       VARCHAR(20)   NOT NULL DEFAULT 'active',
  created_at   DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at   DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY ix_sliders_tenant_id (tenant_id),
  KEY ix_sliders_sort_order (sort_order),
  CONSTRAINT fk_sliders_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- Páginas de ayuda (por tenant, contenido dinámico para el storefront)
-- -----------------------------------------------------------------------------
CREATE TABLE help_pages (
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

-- -----------------------------------------------------------------------------
-- Configuración de tienda (barra superior, redes, contacto)
-- -----------------------------------------------------------------------------
CREATE TABLE store_settings (
  id            CHAR(36)      NOT NULL,
  tenant_id     CHAR(36)      NOT NULL,
  phone         VARCHAR(40)   NOT NULL DEFAULT '',
  schedule      VARCHAR(120)  NOT NULL DEFAULT '',
  support_label VARCHAR(120)  NOT NULL DEFAULT '',
  support_href  VARCHAR(255)  NOT NULL DEFAULT '/help',
  contact_email VARCHAR(255)  NOT NULL DEFAULT '',
  store_url     VARCHAR(500)  NOT NULL DEFAULT '',
  social_links  JSON          NOT NULL,
  created_at    DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at    DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_store_settings_tenant (tenant_id),
  KEY ix_store_settings_tenant_id (tenant_id),
  CONSTRAINT fk_store_settings_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- Productos del catálogo ecommerce (por tenant)
-- Tipos: simple | color | size | size_color
-- -----------------------------------------------------------------------------
CREATE TABLE catalog_products (
  id            CHAR(36)     NOT NULL,
  tenant_id     CHAR(36)     NOT NULL,
  sku           VARCHAR(100) NOT NULL,
  title         VARCHAR(255) NOT NULL,
  description   TEXT         NOT NULL,
  category      VARCHAR(255) NOT NULL DEFAULT '',
  product_type  VARCHAR(30)  NOT NULL DEFAULT 'simple',
  status        VARCHAR(20)  NOT NULL DEFAULT 'active',
  price         INT          NOT NULL DEFAULT 0,
  stock         INT          NOT NULL DEFAULT 0,
  images        JSON         NOT NULL,
  color_images  JSON         NOT NULL,
  variants      JSON         NOT NULL,
  variant_mode  VARCHAR(30)  NULL,
  created_at    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY ix_catalog_products_tenant_id (tenant_id),
  KEY ix_catalog_products_sku (sku),
  CONSTRAINT fk_catalog_products_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- Pedidos (por tenant)
-- -----------------------------------------------------------------------------
CREATE TABLE orders (
  id               CHAR(36)     NOT NULL,
  tenant_id        CHAR(36)     NOT NULL,
  order_number     VARCHAR(30)  NOT NULL,
  customer_id      CHAR(36)     NULL,
  customer_name    VARCHAR(255) NOT NULL,
  customer_email   VARCHAR(255) NOT NULL DEFAULT '',
  customer_phone   VARCHAR(50)  NOT NULL DEFAULT '',
  shipping_address VARCHAR(500) NOT NULL DEFAULT '',
  city             VARCHAR(120) NOT NULL DEFAULT '',
  status           VARCHAR(30)  NOT NULL DEFAULT 'pending',
  payment_status   VARCHAR(30)  NOT NULL DEFAULT 'pending',
  items            JSON         NOT NULL,
  total            INT          NOT NULL DEFAULT 0,
  notes            TEXT         NOT NULL,
  created_at       DATE         NOT NULL,
  PRIMARY KEY (id),
  KEY ix_orders_tenant_id (tenant_id),
  KEY ix_orders_order_number (order_number),
  KEY ix_orders_customer_id (customer_id),
  CONSTRAINT fk_orders_tenant   FOREIGN KEY (tenant_id)   REFERENCES tenants (id),
  CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- Pagos (por tenant, vinculados a pedidos)
-- -----------------------------------------------------------------------------
CREATE TABLE payments (
  id              CHAR(36)     NOT NULL,
  tenant_id       CHAR(36)     NOT NULL,
  payment_number  VARCHAR(30)  NOT NULL,
  order_id        CHAR(36)     NULL,
  order_number    VARCHAR(30)  NOT NULL DEFAULT '',
  customer_name   VARCHAR(255) NOT NULL DEFAULT '',
  amount          INT          NOT NULL DEFAULT 0,
  method          VARCHAR(30)  NOT NULL DEFAULT 'webpay',
  status          VARCHAR(30)  NOT NULL DEFAULT 'pending',
  transaction_ref VARCHAR(120) NOT NULL DEFAULT '',
  notes           TEXT         NOT NULL,
  paid_at         DATE         NULL,
  created_at      DATE         NOT NULL,
  PRIMARY KEY (id),
  KEY ix_payments_tenant_id (tenant_id),
  KEY ix_payments_payment_number (payment_number),
  KEY ix_payments_order_id (order_id),
  CONSTRAINT fk_payments_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id),
  CONSTRAINT fk_payments_order  FOREIGN KEY (order_id)  REFERENCES orders (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- Tickets de soporte (por tenant)
-- -----------------------------------------------------------------------------
CREATE TABLE support_tickets (
  id                 CHAR(36)     NOT NULL,
  tenant_id          CHAR(36)     NOT NULL,
  ticket_number      VARCHAR(30)  NOT NULL,
  subject            VARCHAR(255) NOT NULL,
  description        TEXT         NOT NULL,
  status             VARCHAR(30)  NOT NULL DEFAULT 'open',
  priority           VARCHAR(20)  NOT NULL DEFAULT 'normal',
  created_by_user_id CHAR(36)     NOT NULL,
  created_by_name    VARCHAR(255) NOT NULL DEFAULT '',
  messages           JSON         NOT NULL,
  created_at         DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at         DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_support_tickets_tenant_number (tenant_id, ticket_number),
  KEY ix_support_tickets_tenant_id (tenant_id),
  KEY ix_support_tickets_ticket_number (ticket_number),
  KEY ix_support_tickets_created_by_user_id (created_by_user_id),
  CONSTRAINT fk_support_tickets_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id),
  CONSTRAINT fk_support_tickets_user FOREIGN KEY (created_by_user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
