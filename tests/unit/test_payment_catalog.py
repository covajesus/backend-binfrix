from app.payments.catalog import default_payment_methods, merge_payment_methods


def test_unknown_environment_falls_back_to_sandbox():
    merged = merge_payment_methods(
        {
            "CL": {"webpay": {"enabled": True, "environment": "staging"}},
            "VE": {"zelle": {"enabled": True, "environment": "nope"}},
        }
    )

    assert merged["CL"]["webpay"]["environment"] == "sandbox"
    assert merged["VE"]["zelle"]["environment"] == "sandbox"
    assert merged["VE"]["zelle"]["enabled"] is True


def test_empty_secret_keeps_the_previous_one():
    previous = default_payment_methods()
    previous["VE"]["binance"]["api_secret"] = "keep-me"
    merged = merge_payment_methods(
        {"VE": {"binance": {"enabled": True, "api_secret": ""}}},
        previous,
    )

    assert merged["VE"]["binance"]["api_secret"] == "keep-me"


def test_disabled_methods_stay_off_by_default():
    merged = merge_payment_methods({})

    assert merged["VE"]["zelle"]["enabled"] is False
    assert merged["VE"]["binance"]["enabled"] is False
    assert merged["VE"]["pago_movil"]["enabled"] is False
    assert merged["CO"]["payu"]["enabled"] is False
    assert merged["CO"]["wompi"]["enabled"] is False
    assert merged["CL"]["webpay"]["enabled"] is False
