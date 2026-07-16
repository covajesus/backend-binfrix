from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.core.i18n import resolve_locale, translate_api_message
from app.db.seed import seed_database
from app.db.session import SessionLocal, init_db
from app.routers import (
    auth,
    blog_posts,
    catalog,
    categories,
    contact_messages,
    customers,
    dashboard,
    help_pages,
    landing_pages,
    licenses,
    orders,
    payments,
    platform,
    products,
    roles,
    sliders,
    store,
    store_settings,
    storefront_templates,
    support_tickets,
    tenants,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    import logging

    logger = logging.getLogger("binfrix")
    logger.info("Iniciando API en puerto %s", settings.app_port)
    logger.info("MySQL %s:%s/%s", settings.mysql_host, settings.mysql_port, settings.mysql_database)
    logger.info("CORS origins (%d): %s", len(settings.cors_origin_list), settings.cors_origin_list)

    try:
        init_db()
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()
        logger.info("Base de datos lista")
    except Exception:
        logger.exception("Error al iniciar base de datos")
        raise
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


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    locale = resolve_locale(request.headers.get("accept-language"))
    detail = exc.detail
    if isinstance(detail, str):
        detail = translate_api_message(detail, locale)
    elif isinstance(detail, list):
        detail = [
            {
                **item,
                "msg": translate_api_message(item.get("msg", ""), locale),
            }
            if isinstance(item, dict)
            else item
            for item in detail
        ]
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


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
app.include_router(platform.router, prefix=api_prefix)
app.include_router(sliders.router, prefix=api_prefix)
app.include_router(help_pages.router, prefix=api_prefix)
app.include_router(landing_pages.router, prefix=api_prefix)
app.include_router(support_tickets.router, prefix=api_prefix)
app.include_router(contact_messages.router, prefix=api_prefix)
app.include_router(blog_posts.router, prefix=api_prefix)
app.include_router(store_settings.router, prefix=api_prefix)
app.include_router(storefront_templates.router, prefix=api_prefix)
app.include_router(store.router, prefix=api_prefix)


@app.get("/health")
def health() -> dict[str, str | bool]:
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        db_ok = False

    status = "ok" if db_ok else "degraded"
    return {
        "status": status,
        "service": settings.app_name,
        "database": db_ok,
        "api_prefix": settings.api_prefix,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.app_port, reload=True)
