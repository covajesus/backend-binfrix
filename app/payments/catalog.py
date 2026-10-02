"""Definición y normalización de medios de pago (sandbox o production)."""

from __future__ import annotations

ENVIRONMENTS = ("sandbox", "production")
SECRET_FIELDS = ("api_key", "api_secret")


def _environment(value: object, default: str = "sandbox") -> str:
    env = str(value or default).strip().lower()
    return env if env in ENVIRONMENTS else "sandbox"


def _text(value: object) -> str:
    return str(value or "").strip()


def _enabled(bucket: dict, key: str, default: bool) -> bool:
    raw = bucket.get(key) if isinstance(bucket.get(key), dict) else {}
    if "enabled" not in raw:
        return default
    return bool(raw.get("enabled"))


def _keep_secret(incoming: dict, previous: dict, field: str) -> str:
    value = _text(incoming.get(field))
    if value:
        return value
    return _text(previous.get(field))


def default_payment_methods() -> dict:
    return {
        "CL": {
            "webpay": {"enabled": False, "environment": "sandbox"},
            "transfer": {"enabled": True, "environment": "sandbox"},
        },
        "VE": {
            "pago_movil": {
                "enabled": False,
                "environment": "sandbox",
                "bank": "",
                "rif": "",
                "phone": "",
                "mode": "manual",
            },
            "zelle": {
                "enabled": False,
                "environment": "sandbox",
                "holder_name": "",
                "email": "",
                "phone": "",
            },
            "binance": {
                "enabled": False,
                "environment": "sandbox",
                "merchant_id": "",
                "api_key": "",
                "api_secret": "",
                "currency": "USDT",
            },
        },
        "CO": {
            "payu": {
                "enabled": False,
                "environment": "sandbox",
                "merchant_id": "",
                "account_id": "",
                "api_key": "",
            },
            "wompi": {
                "enabled": False,
                "environment": "sandbox",
                "public_key": "",
                "private_key": "",
                "integrity": "",
            },
            "transfer": {"enabled": True, "environment": "sandbox"},
        },
    }


def merge_payment_methods(raw: dict | None, previous: dict | None = None) -> dict:
    defaults = default_payment_methods()
    source = raw if isinstance(raw, dict) else {}
    prior = previous if isinstance(previous, dict) else {}
    cl = source.get("CL") if isinstance(source.get("CL"), dict) else {}
    ve = source.get("VE") if isinstance(source.get("VE"), dict) else {}
    prior_ve = prior.get("VE") if isinstance(prior.get("VE"), dict) else {}
    prior_co = prior.get("CO") if isinstance(prior.get("CO"), dict) else {}
    co = source.get("CO") if isinstance(source.get("CO"), dict) else {}
    webpay = cl.get("webpay") if isinstance(cl.get("webpay"), dict) else {}
    transfer = cl.get("transfer") if isinstance(cl.get("transfer"), dict) else {}
    pago = ve.get("pago_movil") if isinstance(ve.get("pago_movil"), dict) else {}
    zelle = ve.get("zelle") if isinstance(ve.get("zelle"), dict) else {}
    binance = ve.get("binance") if isinstance(ve.get("binance"), dict) else {}
    prior_binance = prior_ve.get("binance") if isinstance(prior_ve.get("binance"), dict) else {}
    payu = co.get("payu") if isinstance(co.get("payu"), dict) else {}
    prior_payu = prior_co.get("payu") if isinstance(prior_co.get("payu"), dict) else {}
    wompi = co.get("wompi") if isinstance(co.get("wompi"), dict) else {}
    prior_wompi = prior_co.get("wompi") if isinstance(prior_co.get("wompi"), dict) else {}
    co_transfer = co.get("transfer") if isinstance(co.get("transfer"), dict) else {}

    return {
        "CL": {
            "webpay": {
                "enabled": _enabled(cl, "webpay", defaults["CL"]["webpay"]["enabled"]),
                "environment": _environment(webpay.get("environment")),
            },
            "transfer": {
                "enabled": _enabled(cl, "transfer", defaults["CL"]["transfer"]["enabled"]),
                "environment": _environment(transfer.get("environment")),
            },
        },
        "VE": {
            "pago_movil": {
                "enabled": _enabled(ve, "pago_movil", False),
                "environment": _environment(pago.get("environment")),
                "bank": _text(pago.get("bank")),
                "rif": _text(pago.get("rif")),
                "phone": _text(pago.get("phone")),
                "mode": "automatic" if _text(pago.get("mode")).lower() == "automatic" else "manual",
            },
            "zelle": {
                "enabled": _enabled(ve, "zelle", False),
                "environment": _environment(zelle.get("environment")),
                "holder_name": _text(zelle.get("holder_name")),
                "email": _text(zelle.get("email")),
                "phone": _text(zelle.get("phone")),
            },
            "binance": {
                "enabled": _enabled(ve, "binance", False),
                "environment": _environment(binance.get("environment")),
                "merchant_id": _text(binance.get("merchant_id")),
                "api_key": _keep_secret(binance, prior_binance, "api_key"),
                "api_secret": _keep_secret(binance, prior_binance, "api_secret"),
                "currency": _text(binance.get("currency") or "USDT").upper() or "USDT",
            },
        },
        "CO": {
            "payu": {
                "enabled": _enabled(co, "payu", False),
                "environment": _environment(payu.get("environment")),
                "merchant_id": _text(payu.get("merchant_id")),
                "account_id": _text(payu.get("account_id")),
                "api_key": _keep_secret(payu, prior_payu, "api_key"),
            },
            "wompi": {
                "enabled": _enabled(co, "wompi", False),
                "environment": _environment(wompi.get("environment")),
                "public_key": _text(wompi.get("public_key")),
                "private_key": _keep_secret(wompi, prior_wompi, "private_key"),
                "integrity": _keep_secret(wompi, prior_wompi, "integrity"),
            },
            "transfer": {
                "enabled": _enabled(co, "transfer", True),
                "environment": _environment(co_transfer.get("environment")),
            },
        },
    }


def public_payment_methods(methods: dict) -> dict:
    """Quita secretos antes de enviar la config a la tienda pública."""
    safe = merge_payment_methods(methods)
    binance = safe["VE"]["binance"]
    binance["api_key_configured"] = bool(binance.pop("api_key", ""))
    binance["api_secret_configured"] = bool(binance.pop("api_secret", ""))
    payu = safe["CO"]["payu"]
    payu["api_key_configured"] = bool(payu.pop("api_key", ""))
    wompi = safe["CO"]["wompi"]
    wompi["private_key_configured"] = bool(wompi.pop("private_key", ""))
    wompi["integrity_configured"] = bool(wompi.pop("integrity", ""))
    return safe


def admin_payment_methods(methods: dict) -> dict:
    safe = public_payment_methods(methods)
    return safe
