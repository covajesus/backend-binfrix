from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.seed import seed_database
from app.db.session import SessionLocal, init_db
from app.routers import (
    auth,
    catalog,
    categories,
    customers,
    dashboard,
    licenses,
    orders,
    payments,
    products,
    roles,
    store,
    tenants,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="API multi-tenant Binfrix para admin y ecommerce.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = settings.api_prefix
app.include_router(auth.router, prefix=api_prefix)
app.include_router(roles.router, prefix=api_prefix)
app.include_router(tenants.router, prefix=api_prefix)
app.include_router(licenses.router, prefix=api_prefix)
app.include_router(products.router, prefix=api_prefix)
app.include_router(categories.router, prefix=api_prefix)
app.include_router(catalog.router, prefix=api_prefix)
app.include_router(customers.router, prefix=api_prefix)
app.include_router(orders.router, prefix=api_prefix)
app.include_router(payments.router, prefix=api_prefix)
app.include_router(dashboard.router, prefix=api_prefix)
app.include_router(store.router, prefix=api_prefix)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
