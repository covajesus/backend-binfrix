-- =============================================================================
-- Binfrix â€” Esquema completo MySQL
-- Ejecutar en MySQL 8.0+ o MariaDB 10.5+
-- =============================================================================

CREATE DATABASE IF NOT EXISTS binfrix
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE binfrix;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS catalog_products;
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
-- Productos SaaS Binfrix (mÃ³dulos: ecommerce-b2c, pagos, autolavado, etc.)
-- -----------------------------------------------------------------------------
CREATE TABLE platform_products (
  id          VARCHAR(50)  NOT NULL,
  name        VARCHAR(255) NOT NULL,
  description TEXT         NOT NULL,
  is_active   TINYINT(1)   NOT NULL DEFAULT 1,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- MembresÃ­a usuario â†” tenant
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
-- CategorÃ­as del catÃ¡logo ecommerce (por tenant)
-- -----------------------------------------------------------------------------
CREATE TABLE categories (
  id          CHAR(36)     NOT NULL,
  tenant_id   CHAR(36)     NOT NULL,
  name        VARCHAR(255) NOT NULL,
  description TEXT         NOT NULL,
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
-- Productos del catÃ¡logo ecommerce (por tenant)
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
-- =============================================================================
-- Binfrix â€” Datos demo (ejecutar despuÃ©s de schema_mysql.sql)
-- =============================================================================

USE binfrix;

-- Usuario admin: admin@binfrix.com / admin123
INSERT INTO roles (id, slug, name, description) VALUES
('r1000001-0000-4000-8000-000000000001', 'administrador', 'Administrador',
 'Acceso total a la plataforma: clientes, licencias y usuarios.'),
('r1000002-0000-4000-8000-000000000002', 'cliente_tipo_1', 'Cliente tipo 1',
 'Acceso a módulos Binfrix asignados por licencia (operación estándar).'),
('r1000003-0000-4000-8000-000000000003', 'cliente_tipo_2', 'Cliente tipo 2',
 'Acceso a módulos Binfrix con permisos de gestión ampliada.');

INSERT INTO users (id, email, password_hash, name, role_id, is_superadmin, created_at) VALUES
('a1000001-0000-4000-8000-000000000001', 'admin@binfrix.com',
 '$2b$12$S5p3yzdc.Fi1yapqtZeRFej/uQu5Bm7MPg.T6irCnlrskEOgoMKCC',
 'Administrador', 'r1000001-0000-4000-8000-000000000001', 1, NOW(6)),
('a1000002-0000-4000-8000-000000000002', 'cliente1@binfrix.com',
 '$2b$12$.2WJhhfKdMFPmffnTVPeDuBJOatK6HEqKBW/cATjj50sfnf0vjVku',
 'María López', 'r1000002-0000-4000-8000-000000000002', 0, NOW(6)),
('a1000003-0000-4000-8000-000000000003', 'cliente2@binfrix.com',
 '$2b$12$.2WJhhfKdMFPmffnTVPeDuBJOatK6HEqKBW/cATjj50sfnf0vjVku',
 'Carlos Ruiz', 'r1000003-0000-4000-8000-000000000003', 0, NOW(6));

INSERT INTO tenants (id, name, slug, status, created_at) VALUES
('b1000001-0000-4000-8000-000000000001', 'Tienda Demo Binfrix', 'tienda-demo', 'active', NOW(6));

INSERT INTO tenant_memberships (id, tenant_id, user_id, role, created_at) VALUES
('c1000001-0000-4000-8000-000000000001',
 'b1000001-0000-4000-8000-000000000001',
 'a1000001-0000-4000-8000-000000000001',
 'admin', NOW(6)),
('c1000002-0000-4000-8000-000000000002',
 'b1000001-0000-4000-8000-000000000001',
 'a1000002-0000-4000-8000-000000000002',
 'staff', NOW(6)),
('c1000003-0000-4000-8000-000000000003',
 'b1000001-0000-4000-8000-000000000001',
 'a1000003-0000-4000-8000-000000000003',
 'staff', NOW(6));

INSERT INTO platform_products (id, name, description, is_active) VALUES
('autolavado',        'Autolavado',              'Tickets, ventas, cierre de caja y liquidaciÃ³n de lavadores.', 1),
('dynamic-landing',   'Dynamic Landing Page',    'Landings dinÃ¡micas para campaÃ±as y conversiÃ³n.', 1),
('ecommerce-b2b',     'Ecommerce B2B',           'Portal mayorista con intranet y presupuestos.', 1),
('ecommerce-b2c',     'Ecommerce B2C',           'Tienda en lÃ­nea para venta al consumidor final.', 1),
('pagos',             'Pagos',                   'Pasarelas de pago, checkout y conciliaciÃ³n de transacciones.', 1),
('mantencion',        'MantenciÃ³n',              'Soporte tÃ©cnico, respaldos y monitoreo.', 1),
('redes-sociales',    'Redes Sociales',          'GestiÃ³n de perfiles y calendario editorial.', 1),
('ventas-whatsapp',   'Ventas por WhatsApp',     'Canal comercial con pedidos y seguimiento.', 1);

INSERT INTO tenant_licenses (id, tenant_id, platform_product_id, status, plan, starts_at, ends_at, max_users, created_at) VALUES
('d1000001-0000-4000-8000-000000000001', 'b1000001-0000-4000-8000-000000000001', 'ecommerce-b2c', 'active', 'standard', '2025-01-01', '2027-12-31', 10, NOW(6)),
('d1000002-0000-4000-8000-000000000002', 'b1000001-0000-4000-8000-000000000001', 'ecommerce-b2b', 'active', 'standard', '2025-01-01', '2027-12-31', 10, NOW(6)),
('d1000003-0000-4000-8000-000000000003', 'b1000001-0000-4000-8000-000000000001', 'pagos',         'active', 'standard', '2025-01-01', '2027-12-31', 10, NOW(6));

INSERT INTO categories (id, tenant_id, name, description, status, created_at) VALUES
('e1000001-0000-4000-8000-000000000001', 'b1000001-0000-4000-8000-000000000001', 'Calzado',     'Zapatillas y calzado deportivo',        'active', '2025-10-01'),
('e1000002-0000-4000-8000-000000000002', 'b1000001-0000-4000-8000-000000000001', 'Ropa',        'Prendas y accesorios de vestir',        'active', '2025-10-01'),
('e1000003-0000-4000-8000-000000000003', 'b1000001-0000-4000-8000-000000000001', 'Accesorios',  'Bolsos, mochilas y complementos',       'active', '2025-10-01');

INSERT INTO catalog_products (
  id, tenant_id, sku, title, description, category, product_type, status,
  price, stock, images, color_images, variants, variant_mode, created_at, updated_at
) VALUES
(
  'f1000001-0000-4000-8000-000000000001',
  'b1000001-0000-4000-8000-000000000001',
  'ZAP-001', 'Runner Pro Sneaker', 'Zapatilla liviana para entrenamiento y uso urbano.',
  'Calzado', 'size_color', 'active', 0, 42,
  JSON_ARRAY(),
  JSON_OBJECT('#111827', JSON_ARRAY(), '#f9fafb', JSON_ARRAY()),
  JSON_ARRAY(
    JSON_OBJECT('id','var-1','sku','ZAP-001-40-BLK','size','40','color','#111827','price',89990,'stock',12),
    JSON_OBJECT('id','var-2','sku','ZAP-001-42-BLK','size','42','color','#111827','price',89990,'stock',18),
    JSON_OBJECT('id','var-3','sku','ZAP-001-42-WHT','size','42','color','#f9fafb','price',89990,'stock',12)
  ),
  'size_color', NOW(6), NOW(6)
),
(
  'f1000002-0000-4000-8000-000000000002',
  'b1000001-0000-4000-8000-000000000001',
  'POL-014', 'Essential Hoodie', 'PolerÃ³n de algodÃ³n con bolsillo frontal.',
  'Ropa', 'simple', 'active', 45990, 18,
  JSON_ARRAY(), JSON_OBJECT(), JSON_ARRAY(),
  NULL, NOW(6), NOW(6)
),
(
  'f1000003-0000-4000-8000-000000000003',
  'b1000001-0000-4000-8000-000000000001',
  'BOL-008', 'Urban Sport Bag', 'Bolso compacto con compartimento para zapatillas.',
  'Accesorios', 'simple', 'inactive', 32990, 0,
  JSON_ARRAY(), JSON_OBJECT(), JSON_ARRAY(),
  NULL, NOW(6), NOW(6)
);

INSERT INTO customers (id, tenant_id, first_name, last_name, email, phone, city, status, notes, created_at) VALUES
('g1000001-0000-4000-8000-000000000001', 'b1000001-0000-4000-8000-000000000001', 'MarÃ­a', 'GarcÃ­a',  'maria.garcia@email.com',  '+56 9 8765 4321', 'Santiago',    'active',   '', '2025-11-12'),
('g1000002-0000-4000-8000-000000000002', 'b1000001-0000-4000-8000-000000000001', 'Carlos', 'Ruiz',   'carlos.ruiz@email.com',   '+56 9 7654 3210', 'ValparaÃ­so',  'active',   '', '2025-12-03'),
('g1000003-0000-4000-8000-000000000003', 'b1000001-0000-4000-8000-000000000001', 'Ana',   'MartÃ­n',  'ana.martin@email.com',    '+56 9 6543 2109', 'ConcepciÃ³n',  'inactive', '', '2026-01-18');

INSERT INTO orders (
  id, tenant_id, order_number, customer_id, customer_name, customer_email, customer_phone,
  shipping_address, city, status, payment_status, items, total, notes, created_at
) VALUES
(
  'h1000001-0000-4000-8000-000000000001',
  'b1000001-0000-4000-8000-000000000001',
  'PED-0001', 'g1000001-0000-4000-8000-000000000001',
  'MarÃ­a GarcÃ­a', 'maria.garcia@email.com', '+56 9 8765 4321',
  'Av. Providencia 1200, Depto 402', 'Santiago',
  'delivered', 'paid',
  JSON_ARRAY(JSON_OBJECT('id','line-1','product_title','Runner Pro Sneaker','sku','ZAP-001-42-BLK','quantity',1,'unit_price',89990)),
  89990, '', '2026-03-08'
),
(
  'h1000002-0000-4000-8000-000000000002',
  'b1000001-0000-4000-8000-000000000001',
  'PED-0002', 'g1000002-0000-4000-8000-000000000002',
  'Carlos Ruiz', 'carlos.ruiz@email.com', '+56 9 7654 3210',
  'Calle Prat 88', 'ValparaÃ­so',
  'pending', 'pending',
  JSON_ARRAY(JSON_OBJECT('id','line-2','product_title','Essential Hoodie','sku','POL-014','quantity',2,'unit_price',45990)),
  91980, '', '2026-03-10'
),
(
  'h1000003-0000-4000-8000-000000000003',
  'b1000001-0000-4000-8000-000000000001',
  'PED-0003', 'g1000003-0000-4000-8000-000000000003',
  'Ana MartÃ­n', 'ana.martin@email.com', '+56 9 6543 2109',
  'Los Carrera 455', 'ConcepciÃ³n',
  'shipped', 'paid',
  JSON_ARRAY(JSON_OBJECT('id','line-3','product_title','Urban Sport Bag','sku','BOL-008','quantity',1,'unit_price',32990)),
  32990, '', '2026-03-01'
);

INSERT INTO payments (
  id, tenant_id, payment_number, order_id, order_number, customer_name,
  amount, method, status, transaction_ref, notes, paid_at, created_at
) VALUES
(
  'i1000001-0000-4000-8000-000000000001',
  'b1000001-0000-4000-8000-000000000001',
  'PAG-0001', 'h1000001-0000-4000-8000-000000000001', 'PED-0001', 'MarÃ­a GarcÃ­a',
  89990, 'webpay', 'completed', 'WP-92837461', 'Pago confirmado automÃ¡ticamente.', '2026-03-08', '2026-03-08'
),
(
  'i1000002-0000-4000-8000-000000000002',
  'b1000001-0000-4000-8000-000000000001',
  'PAG-0002', 'h1000002-0000-4000-8000-000000000002', 'PED-0002', 'Carlos Ruiz',
  91980, 'transfer', 'pending', 'TRF-004512', 'Esperando comprobante bancario.', NULL, '2026-03-10'
),
(
  'i1000003-0000-4000-8000-000000000003',
  'b1000001-0000-4000-8000-000000000001',
  'PAG-0003', 'h1000003-0000-4000-8000-000000000003', 'PED-0003', 'Ana MartÃ­n',
  32990, 'card', 'completed', 'TC-7712044', '', '2026-03-01', '2026-03-01'
);
