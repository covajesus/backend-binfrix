"""Añade columnas faltantes en store_settings (MySQL / tablas ya existentes)."""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.db.session import engine


def _migrate_legacy_webpay_columns(cols: set[str]) -> None:
    if "webpay_enabled" not in cols or "payment_gateway_enabled" not in cols:
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE store_settings SET "
                "payment_gateway_enabled = webpay_enabled "
                "WHERE payment_gateway_enabled = 0 AND webpay_enabled = 1"
            )
        )
        conn.execute(
            text(
                "UPDATE store_settings SET "
                "payment_gateway_provider = 'transbank_cl' "
                "WHERE payment_gateway_provider = '' AND webpay_enabled = 1"
            )
        )
        conn.execute(
            text(
                "UPDATE store_settings SET "
                "payment_gateway_merchant_id = webpay_commerce_code "
                "WHERE payment_gateway_merchant_id = '' "
                "AND webpay_commerce_code IS NOT NULL AND webpay_commerce_code != ''"
            )
        )
        conn.execute(
            text(
                "UPDATE store_settings SET "
                "payment_gateway_api_key = webpay_api_key "
                "WHERE payment_gateway_api_key = '' "
                "AND webpay_api_key IS NOT NULL AND webpay_api_key != ''"
            )
        )
        conn.execute(
            text(
                "UPDATE store_settings SET "
                "payment_gateway_environment = webpay_environment "
                "WHERE payment_gateway_environment = 'sandbox' "
                "AND webpay_environment IS NOT NULL AND webpay_environment != ''"
            )
        )


def ensure_store_settings_columns() -> list[str]:
    """ALTER TABLE para columnas nuevas; create_all no modifica tablas existentes."""
    inspector = inspect(engine)
    if "store_settings" not in inspector.get_table_names():
        return []

    cols = {c["name"] for c in inspector.get_columns("store_settings")}
    added: list[str] = []

    pending: list[tuple[str, str]] = []
    if "storefront_template" not in cols:
        pending.append(
            (
                "storefront_template",
                "ALTER TABLE store_settings "
                "ADD COLUMN storefront_template VARCHAR(40) NOT NULL DEFAULT 'sports'",
            )
        )
    if "multilingual_enabled" not in cols:
        pending.append(
            (
                "multilingual_enabled",
                "ALTER TABLE store_settings "
                "ADD COLUMN multilingual_enabled TINYINT(1) NOT NULL DEFAULT 0",
            )
        )
    if "default_locale" not in cols:
        pending.append(
            (
                "default_locale",
                "ALTER TABLE store_settings "
                "ADD COLUMN default_locale VARCHAR(5) NOT NULL DEFAULT 'es'",
            )
        )
    if "account_label" not in cols:
        pending.append(
            (
                "account_label",
                "ALTER TABLE store_settings ADD COLUMN account_label VARCHAR(120) NOT NULL DEFAULT ''",
            )
        )
    if "account_href" not in cols:
        pending.append(
            (
                "account_href",
                "ALTER TABLE store_settings ADD COLUMN account_href VARCHAR(255) NOT NULL DEFAULT '/help'",
            )
        )
    if "promo_messages" not in cols:
        pending.append(
            (
                "promo_messages",
                "ALTER TABLE store_settings ADD COLUMN promo_messages JSON NULL",
            )
        )
    if "header_links" not in cols:
        pending.append(
            (
                "header_links",
                "ALTER TABLE store_settings ADD COLUMN header_links JSON NULL",
            )
        )
    if "store_logo_url" not in cols:
        pending.append(
            (
                "store_logo_url",
                "ALTER TABLE store_settings ADD COLUMN store_logo_url TEXT NULL",
            )
        )
    if "theme_colors" not in cols:
        pending.append(
            (
                "theme_colors",
                "ALTER TABLE store_settings ADD COLUMN theme_colors JSON NULL",
            )
        )
    if "payment_gateway_enabled" not in cols:
        pending.append(
            (
                "payment_gateway_enabled",
                "ALTER TABLE store_settings "
                "ADD COLUMN payment_gateway_enabled TINYINT(1) NOT NULL DEFAULT 0",
            )
        )
    if "payment_gateway_provider" not in cols:
        pending.append(
            (
                "payment_gateway_provider",
                "ALTER TABLE store_settings "
                "ADD COLUMN payment_gateway_provider VARCHAR(40) NOT NULL DEFAULT ''",
            )
        )
    if "payment_gateway_merchant_id" not in cols:
        pending.append(
            (
                "payment_gateway_merchant_id",
                "ALTER TABLE store_settings "
                "ADD COLUMN payment_gateway_merchant_id VARCHAR(40) NOT NULL DEFAULT ''",
            )
        )
    if "payment_gateway_api_key" not in cols:
        pending.append(
            (
                "payment_gateway_api_key",
                "ALTER TABLE store_settings "
                "ADD COLUMN payment_gateway_api_key VARCHAR(255) NOT NULL DEFAULT ''",
            )
        )
    if "payment_gateway_environment" not in cols:
        pending.append(
            (
                "payment_gateway_environment",
                "ALTER TABLE store_settings "
                "ADD COLUMN payment_gateway_environment VARCHAR(20) NOT NULL DEFAULT 'sandbox'",
            )
        )

    if "billing_enabled" not in cols:
        pending.append(
            (
                "billing_enabled",
                "ALTER TABLE store_settings "
                "ADD COLUMN billing_enabled TINYINT(1) NOT NULL DEFAULT 0",
            )
        )
    if "billing_country" not in cols:
        pending.append(
            (
                "billing_country",
                "ALTER TABLE store_settings "
                "ADD COLUMN billing_country VARCHAR(5) NOT NULL DEFAULT 'CL'",
            )
        )
    if "billing_provider" not in cols:
        pending.append(
            (
                "billing_provider",
                "ALTER TABLE store_settings "
                "ADD COLUMN billing_provider VARCHAR(40) NOT NULL DEFAULT ''",
            )
        )
    if "billing_api_key" not in cols:
        pending.append(
            (
                "billing_api_key",
                "ALTER TABLE store_settings "
                "ADD COLUMN billing_api_key VARCHAR(255) NOT NULL DEFAULT ''",
            )
        )
    if "billing_username" not in cols:
        pending.append(
            (
                "billing_username",
                "ALTER TABLE store_settings "
                "ADD COLUMN billing_username VARCHAR(255) NOT NULL DEFAULT ''",
            )
        )
    if "billing_branch" not in cols:
        pending.append(
            (
                "billing_branch",
                "ALTER TABLE store_settings "
                "ADD COLUMN billing_branch VARCHAR(120) NOT NULL DEFAULT 'Casa Matriz'",
            )
        )
    if "billing_emitter_rut" not in cols:
        pending.append(
            (
                "billing_emitter_rut",
                "ALTER TABLE store_settings "
                "ADD COLUMN billing_emitter_rut VARCHAR(20) NOT NULL DEFAULT ''",
            )
        )
    if "billing_emitter_name" not in cols:
        pending.append(
            (
                "billing_emitter_name",
                "ALTER TABLE store_settings "
                "ADD COLUMN billing_emitter_name VARCHAR(255) NOT NULL DEFAULT ''",
            )
        )
    if "billing_emitter_activity" not in cols:
        pending.append(
            (
                "billing_emitter_activity",
                "ALTER TABLE store_settings "
                "ADD COLUMN billing_emitter_activity VARCHAR(255) NOT NULL DEFAULT ''",
            )
        )
    if "billing_emitter_address" not in cols:
        pending.append(
            (
                "billing_emitter_address",
                "ALTER TABLE store_settings "
                "ADD COLUMN billing_emitter_address VARCHAR(255) NOT NULL DEFAULT ''",
            )
        )
    if "billing_emitter_commune" not in cols:
        pending.append(
            (
                "billing_emitter_commune",
                "ALTER TABLE store_settings "
                "ADD COLUMN billing_emitter_commune VARCHAR(120) NOT NULL DEFAULT ''",
            )
        )
    if "billing_emitter_city" not in cols:
        pending.append(
            (
                "billing_emitter_city",
                "ALTER TABLE store_settings "
                "ADD COLUMN billing_emitter_city VARCHAR(120) NOT NULL DEFAULT ''",
            )
        )

    if not pending:
        _migrate_legacy_webpay_columns(cols)
        return added

    with engine.begin() as conn:
        for name, sql in pending:
            conn.execute(text(sql))
            added.append(name)

    cols.update(added)
    _migrate_legacy_webpay_columns(cols)

    # JSON columns sin DEFAULT en MySQL: rellenar vacíos
    with engine.begin() as conn:
        if "promo_messages" in added or "promo_messages" in cols:
            conn.execute(
                text(
                    "UPDATE store_settings SET promo_messages = '[]' "
                    "WHERE promo_messages IS NULL"
                )
            )
        if "header_links" in added or "header_links" in cols:
            conn.execute(
                text(
                    "UPDATE store_settings SET header_links = '[]' "
                    "WHERE header_links IS NULL"
                )
            )
        if "theme_colors" in added or "theme_colors" in cols:
            conn.execute(
                text(
                    "UPDATE store_settings SET theme_colors = '{}' "
                    "WHERE theme_colors IS NULL"
                )
            )

    return added
