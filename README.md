# Binfrix Backend API

API REST **multi-tenant** en **FastAPI** + **SQLAlchemy** + **MySQL** para el panel admin y el ecommerce.

## Requisitos

- Python 3.11+
- MySQL 8.0+ (o MariaDB 10.5+)

## Base de datos MySQL

### Scripts SQL (`backend/scripts/`)

| Archivo | Contenido |
|---------|-----------|
| **`full_mysql.sql`** | Todo en uno: BD + tablas + datos demo |
| `schema_mysql.sql` | Solo creación de tablas |
| `seed_mysql.sql` | Solo datos demo |

**Ejecutar todo:**

```bash
mysql -u root -p < scripts/full_mysql.sql
```

O en MySQL Workbench / phpMyAdmin: abre y ejecuta `scripts/full_mysql.sql`.

**Tablas creadas (10):**
`users`, `tenants`, `platform_products`, `tenant_memberships`, `tenant_licenses`, `categories`, `customers`, `catalog_products`, `orders`, `payments`

**Datos demo incluidos:**
- Usuario: `admin@binfrix.com` / `admin123`
- Tenant: `tienda-demo`
- 8 productos Binfrix, 3 licencias, categorías, catálogo, clientes, pedidos y pagos

2. Copia `.env.example` a `.env` y configura:

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=binfrix
MYSQL_PASSWORD=tu_password
MYSQL_DATABASE=binfrix
```

En el servidor (`/var/www/api.binfrix.io/public_html/`) crea el archivo `.env` con las credenciales reales de MySQL. Sin ese archivo la API intenta conectar como `root` y falla con error 1698.

3. Al arrancar la API se crean las tablas y el seed demo automáticamente.

## Inicio rápido

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8097
# o: python -m app.main  (usa APP_PORT del .env, por defecto 8097)
```

Documentación: [http://localhost:8097/docs](http://localhost:8097/docs)

## Credenciales demo

| Campo    | Valor               |
|----------|---------------------|
| Email    | `admin@binfrix.com` |
| Password | `admin123`          |

**Tenant demo:** `tienda-demo` (slug) — usar en header `X-Tenant-ID: tienda-demo`

## Multi-tenant

Cada empresa (tenant) tiene sus propios datos aislados:

- Usuarios y membresías por tenant
- Licencias de productos Binfrix (ecommerce-b2c, pagos, etc.)
- Catálogo, categorías, clientes, pedidos y pagos

### Headers requeridos (rutas admin)

```
Authorization: Bearer <token>
X-Tenant-ID: tienda-demo
```

## Endpoints principales

### Auth
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Login (devuelve token + tenants) |
| GET | `/api/v1/auth/me` | Usuario actual |

### Tenants y licencias
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/tenants` | Tenants del usuario |
| POST | `/api/v1/tenants` | Crear tenant |
| GET | `/api/v1/tenants/current` | Tenant activo |
| GET | `/api/v1/tenants/users` | Usuarios del tenant |
| POST | `/api/v1/tenants/users` | Invitar usuario |
| GET | `/api/v1/platform-products` | Productos SaaS Binfrix |
| GET | `/api/v1/licenses` | Licencias del tenant |
| POST | `/api/v1/licenses` | Activar licencia |

### Productos Binfrix (selector admin)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/products` | Módulos con licencia activa |
| GET | `/api/v1/products/{id}` | Detalle módulo |

### Ecommerce admin (por tenant)
| Método | Ruta | Descripción |
|--------|------|-------------|
| CRUD | `/api/v1/categories` | Categorías |
| CRUD | `/api/v1/catalog` | Productos catálogo |
| CRUD | `/api/v1/customers` | Clientes |
| CRUD | `/api/v1/orders` | Pedidos |
| CRUD | `/api/v1/payments` | Pagos |
| GET | `/api/v1/dashboard?product_id=` | Métricas dashboard |

### Store público (ecommerce frontend)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/store/{slug}/info` | Info tienda |
| GET | `/api/v1/store/{slug}/categories` | Categorías activas |
| GET | `/api/v1/store/{slug}/catalog` | Productos activos |
| GET | `/api/v1/store/{slug}/catalog/{id}` | Detalle producto |
| POST | `/api/v1/store/{slug}/orders` | Crear pedido |

## Ejemplo login

```bash
curl -X POST http://localhost:8097/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@binfrix.com\",\"password\":\"admin123\"}"
```

```bash
curl http://localhost:8097/api/v1/catalog \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: tienda-demo"
```

## Variables de entorno

```env
SECRET_KEY=change-me-to-a-random-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=root
MYSQL_PASSWORD=tu_password
MYSQL_DATABASE=binfrix
```

Alternativa con URL completa:

```env
DATABASE_URL=mysql+pymysql://binfrix:tu_password@127.0.0.1:3307/binfrix?charset=utf8mb4
```

## Estructura

```
app/
├── main.py
├── config.py
├── db/              # SQLAlchemy + seed
├── models/          # Tenant, User, License, Catalog, Order...
├── schemas/         # Pydantic
├── core/            # Auth, tenant context
├── routers/         # API routes
└── utils/           # Helpers catálogo, pedidos, pagos
```

## Integración frontends

**Admin** (`admin-frontend`):
```env
VITE_API_URL=http://localhost:8097
```

**Ecommerce** (`ecommerce`):
```env
VITE_API_URL=http://localhost:8097
VITE_STORE_SLUG=tienda-demo
```
