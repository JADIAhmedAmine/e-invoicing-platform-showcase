from __future__ import annotations

from .base import ProviderInvoice, ProviderResult, ProviderStatusResult, ValidationResult
from ..invoicepilot.statuses import InvoicePilotStatus, ProviderName


class FuturePDPProvider:
    name = ProviderName.FUTURE_PDP.value

    def validate_payload(self, invoice: ProviderInvoice) -> ValidationResult:
        return ValidationResult(
            valid=False,
            errors=[
                "Le connecteur PDP n'est pas encore actif. InvoicePilot le prépare comme provider futur."
            ],
        )

    def submit_invoice(self, invoice: ProviderInvoice) -> ProviderResult:
        return ProviderResult(
            ok=False,
            provider_name=self.name,
            internal_status=InvoicePilotStatus.ERROR.value,
            user_message="Le routage PDP sera disponible dans une version future.",
            technical_details={"todo": "Implement PDP partner API adapter."},
        )

    def get_status(self, external_invoice_id: str) -> ProviderStatusResult:
        return ProviderStatusResult(
            provider_name=self.name,
            external_invoice_id=external_invoice_id,
            internal_status=InvoicePilotStatus.ERROR.value,
            external_status="NOT_IMPLEMENTED",
            raw_response={"todo": "Implement PDP status mapping."},
        )

    def cancel_invoice(self, external_invoice_id: str) -> ProviderResult:
        return ProviderResult(
            ok=False,
            provider_name=self.name,
            external_invoice_id=external_invoice_id,
            internal_status=InvoicePilotStatus.ERROR.value,
            user_message="L'annulation via PDP sera disponible dans une version future.",
            technical_details={"todo": "Implement PDP cancellation."},
        )
