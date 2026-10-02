"""Compra real contra la API local de la tienda demo.

Enciende todos los medios en sandbox, prueba cada uno y deja la tienda
en Venezuela con Pago móvil, Zelle y Binance activos.
"""

import uuid

import httpx
import pytest

API = "http://localhost:8097/api/v1"
STORE = f"{API}/store/tienda-demo"
DEMO_EMAIL = "cliente1@binfrix.com"
DEMO_PASSWORD = "cliente123"


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=STORE, timeout=40.0) as http:
        try:
            health = http.get("/settings")
        except httpx.HTTPError as exc:
            pytest.skip(f"API no disponible: {exc}")
        if health.status_code != 200:
            pytest.skip(f"API respondió {health.status_code}")
        yield http


@pytest.fixture(scope="module")
def enabled_store(client):
    del client
    with httpx.Client(base_url=API, timeout=40.0) as admin:
        login = admin.post(
            "/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        )
        assert login.status_code == 200, login.text
        headers = {
            "Authorization": f"Bearer {login.json()['token']}",
            "X-Tenant-ID": "tienda-demo",
        }
        current = admin.get("/store-settings", headers=headers)
        assert current.status_code == 200, current.text
        methods = current.json()["payment_methods"]
        for bucket in methods.values():
            if not isinstance(bucket, dict):
                continue
            for block in bucket.values():
                if isinstance(block, dict) and "enabled" in block:
                    block["enabled"] = True
                    block["environment"] = "sandbox"
        updated = admin.patch(
            "/store-settings",
            headers=headers,
            json={"payment_country": "VE", "payment_methods": methods},
        )
        assert updated.status_code == 200, updated.text
        yield
        admin.patch(
            "/store-settings",
            headers=headers,
            json={"payment_country": "VE"},
        )


@pytest.fixture(scope="module")
def settings(client, enabled_store):
    del enabled_store
    body = client.get("/settings").json()
    assert body["payment_country"] == "VE"
    assert body["payment_methods"]["VE"]["pago_movil"]["enabled"] is True
    return body


def _create_order(client):
    suffix = uuid.uuid4().hex[:8]
    response = client.post(
        "/orders",
        json={
            "customer_name": "Prueba Pagos",
            "customer_email": f"pagos.{suffix}@binfrix.test",
            "customer_phone": "+56911111111",
            "shipping_address": "Calle Prueba 123",
            "city": "Santiago",
            "shipping_amount": 0,
            "notes": "Pedido de prueba automatizada",
            "items": [
                {
                    "product_title": "Anillo de prueba",
                    "sku": "TEST-PAY",
                    "quantity": 1,
                    "unit_price": 1000,
                }
            ],
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["order_number"]
    assert body["payment_status"] == "pending"
    return body


def test_catalog_and_settings_are_public(client, settings):
    del settings
    catalog = client.get("/catalog")
    assert catalog.status_code == 200
    assert catalog.json()


@pytest.mark.parametrize(
    ("method", "provider_id"),
    [
        ("zelle", "zelle_ve"),
        ("binance", "binance_ve"),
        ("wompi", "wompi_co"),
    ],
)
def test_sandbox_gateway_marks_order_paid(client, settings, method, provider_id):
    del settings
    order = _create_order(client)
    session = client.post("/payments/session", json={"order_id": order["id"], "method": method})
    assert session.status_code == 200, session.text
    token = session.json()["token"]
    assert token == f"sandbox:{provider_id}:{order['order_number'][:26]}"

    done = client.post("/payments/sandbox", json={"token": token})
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "paid"
    assert done.json()["order_number"] == order["order_number"]


def test_pago_movil_sandbox_reference(client, settings):
    del settings
    order = _create_order(client)
    rejected = client.post(
        "/payments/mobile",
        json={"order_id": order["id"], "reference": "000000"},
    )
    assert rejected.status_code == 400

    paid = client.post(
        "/payments/mobile",
        json={"order_id": order["id"], "reference": "123456"},
    )
    assert paid.status_code == 200, paid.text
    assert paid.json()["status"] == "paid"


def test_webpay_sandbox_opens_transbank(client, settings):
    del settings
    order = _create_order(client)
    session = client.post("/payments/session", json={"order_id": order["id"], "method": "webpay"})
    assert session.status_code == 200, session.text
    assert "webpay3gint.transbank.cl" in session.json()["url"]
    assert session.json()["token"]


def test_payu_session_opens_sandbox_checkout(client, settings):
    del settings
    order = _create_order(client)
    session = client.post("/payments/session", json={"order_id": order["id"], "method": "payu"})
    assert session.status_code == 200, session.text
    assert "sandbox.checkout.payulatam.com" in session.json()["url"]


def test_transfer_is_manual_and_not_a_gateway(client, settings):
    del settings
    order = _create_order(client)
    response = client.post("/payments/session", json={"order_id": order["id"], "method": "transfer"})
    assert response.status_code == 400
    assert order["payment_status"] == "pending"
