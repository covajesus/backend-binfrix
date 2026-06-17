from app.billing_providers.base import BillingProvider
from app.billing_providers.simplefactura_cl import SimpleFacturaClProvider

_PROVIDERS: dict[str, BillingProvider] = {
    SimpleFacturaClProvider.provider_id: SimpleFacturaClProvider(),
}


def get_billing_provider(provider_id: str) -> BillingProvider | None:
    key = (provider_id or "").strip().lower()
    return _PROVIDERS.get(key)


def get_provider_label(provider_id: str) -> str:
    labels = {
        SimpleFacturaClProvider.provider_id: "SimpleFactura",
    }
    return labels.get((provider_id or "").strip().lower(), provider_id)
