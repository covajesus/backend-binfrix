import hashlib

import httpx

from app.payment_providers.base import PaymentGatewayConfig
from app.payment_providers.binance_ve import BinanceVeProvider
from app.payment_providers.payu_co import PayuCoProvider
from app.payment_providers.transbank_cl import TransbankClProvider
from app.payment_providers.wompi_co import WompiCoProvider
from app.payment_providers.zelle_ve import ZelleVeProvider


def _config(provider_id: str, environment: str = "sandbox", **extra) -> PaymentGatewayConfig:
    return PaymentGatewayConfig(
        provider_id=provider_id,
        merchant_id=extra.get("merchant_id", ""),
        api_key=extra.get("api_key", ""),
        environment=environment,
        base_url=extra.get("base_url", ""),
        api_secret=extra.get("api_secret", ""),
        currency=extra.get("currency", ""),
        private_key=extra.get("private_key", ""),
    )


def test_zelle_sandbox_token_does_not_redirect():
    provider = ZelleVeProvider()
    config = provider.resolve_config(True, "", "", "sandbox")
    session = provider.init_session(config, "PED-0001", "sess", 1000, "http://return")

    assert session.token == "sandbox:zelle_ve:PED-0001"
    assert session.redirect_url == ""
    assert provider.commit_session(config, session.token).success is True


def test_zelle_production_stays_manual():
    provider = ZelleVeProvider()
    config = provider.resolve_config(True, "holder", "mail@test.com", "production")
    session = provider.init_session(config, "PED-0002", "sess", 1000, "http://return")

    assert session.token.startswith("manual:zelle_ve:")
    assert provider.commit_session(config, session.token).success is False


def test_binance_sandbox_is_local():
    provider = BinanceVeProvider()
    config = provider.resolve_config(True, "", "", "sandbox", currency="USDT")
    session = provider.init_session(config, "PED-0003", "sess", 2500, "http://return")

    assert session.token == "sandbox:binance_ve:PED-0003"
    assert session.redirect_url == ""
    assert provider.commit_session(config, session.token).success is True


def test_payu_sandbox_uses_public_checkout_and_signature():
    provider = PayuCoProvider()
    config = provider.resolve_config(True, "", "", "sandbox")
    session = provider.init_session(config, "PED-0004", "sess", 15000, "http://return")

    assert "sandbox.checkout.payulatam.com" in session.redirect_url
    assert "test=1" in session.redirect_url
    expected = hashlib.md5(
        f"{config.api_key}~{config.merchant_id}~PED-0004~15000.00~COP".encode()
    ).hexdigest()
    assert provider.signature(config, "PED-0004", "15000.00") == expected


def test_wompi_without_keys_stays_in_local_sandbox():
    provider = WompiCoProvider()
    config = provider.resolve_config(True, "", "", "sandbox")
    session = provider.init_session(config, "PED-0005", "sess", 9000, "http://return")

    assert session.token == "sandbox:wompi_co:PED-0005"
    assert provider.commit_session(config, session.token).success is True


def test_transbank_sandbox_posts_to_integration_host(monkeypatch):
    captured = {}

    def fake_post(url, json, headers, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            json={"token": "token_ws_test", "url": "https://webpay3gint.transbank.cl/webpayserver/initTransaction"},
            request=request,
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = TransbankClProvider()
    config = provider.resolve_config(True, "", "", "sandbox")
    session = provider.init_session(config, "PED-0006", "sess", 4990, "http://return")

    assert captured["url"].startswith("https://webpay3gint.transbank.cl/")
    assert captured["headers"]["Tbk-Api-Key-Id"] == config.merchant_id
    assert session.token == "token_ws_test"
    assert "webpay3gint.transbank.cl" in session.redirect_url
