-- =============================================================================
-- Binfrix — Datos demo (ejecutar después de schema_mysql.sql)
-- =============================================================================

USE binfrix;

INSERT INTO roles (id, slug, name, description) VALUES
('r1000001-0000-4000-8000-000000000001', 'administrador', 'Administrador',
 'Acceso total a la plataforma: clientes, licencias y usuarios.'),
('r1000002-0000-4000-8000-000000000002', 'cliente_tipo_1', 'Cliente tipo 1',
 'Acceso a módulos Binfrix asignados por licencia (operación estándar).'),
('r1000003-0000-4000-8000-000000000003', 'cliente_tipo_2', 'Cliente tipo 2',
 'Acceso a módulos Binfrix con permisos de gestión ampliada.');

-- Usuarios demo:
-- admin@binfrix.com / admin123
-- cliente1@binfrix.com / cliente123
-- cliente2@binfrix.com / cliente123
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
('autolavado',        'Autolavado',              'Tickets, ventas, cierre de caja y liquidación de lavadores.', 1),
('dynamic-landing',   'Dynamic Landing Page',    'Landings dinámicas para campañas y conversión.', 1),
('ecommerce-b2b',     'Ecommerce B2B',           'Portal mayorista con intranet y presupuestos.', 1),
('ecommerce-b2c',     'Ecommerce B2C',           'Tienda en línea para venta al consumidor final.', 1),
('pagos',             'Pagos',                   'Pasarelas de pago, checkout y conciliación de transacciones.', 1),
('mantencion',        'Mantención',              'Soporte técnico, respaldos y monitoreo.', 1),
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
  'POL-014', 'Essential Hoodie', 'Polerón de algodón con bolsillo frontal.',
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
('g1000001-0000-4000-8000-000000000001', 'b1000001-0000-4000-8000-000000000001', 'María', 'García',  'maria.garcia@email.com',  '+56 9 8765 4321', 'Santiago',    'active',   '', '2025-11-12'),
('g1000002-0000-4000-8000-000000000002', 'b1000001-0000-4000-8000-000000000001', 'Carlos', 'Ruiz',   'carlos.ruiz@email.com',   '+56 9 7654 3210', 'Valparaíso',  'active',   '', '2025-12-03'),
('g1000003-0000-4000-8000-000000000003', 'b1000001-0000-4000-8000-000000000001', 'Ana',   'Martín',  'ana.martin@email.com',    '+56 9 6543 2109', 'Concepción',  'inactive', '', '2026-01-18');

INSERT INTO orders (
  id, tenant_id, order_number, customer_id, customer_name, customer_email, customer_phone,
  shipping_address, city, status, payment_status, items, total, notes, created_at
) VALUES
(
  'h1000001-0000-4000-8000-000000000001',
  'b1000001-0000-4000-8000-000000000001',
  'PED-0001', 'g1000001-0000-4000-8000-000000000001',
  'María García', 'maria.garcia@email.com', '+56 9 8765 4321',
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
  'Calle Prat 88', 'Valparaíso',
  'pending', 'pending',
  JSON_ARRAY(JSON_OBJECT('id','line-2','product_title','Essential Hoodie','sku','POL-014','quantity',2,'unit_price',45990)),
  91980, '', '2026-03-10'
),
(
  'h1000003-0000-4000-8000-000000000003',
  'b1000001-0000-4000-8000-000000000001',
  'PED-0003', 'g1000003-0000-4000-8000-000000000003',
  'Ana Martín', 'ana.martin@email.com', '+56 9 6543 2109',
  'Los Carrera 455', 'Concepción',
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
  'PAG-0001', 'h1000001-0000-4000-8000-000000000001', 'PED-0001', 'María García',
  89990, 'webpay', 'completed', 'WP-92837461', 'Pago confirmado automáticamente.', '2026-03-08', '2026-03-08'
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
  'PAG-0003', 'h1000003-0000-4000-8000-000000000003', 'PED-0003', 'Ana Martín',
  32990, 'card', 'completed', 'TC-7712044', '', '2026-03-01', '2026-03-01'
);
