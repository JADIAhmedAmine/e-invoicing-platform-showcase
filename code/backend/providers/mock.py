from __future__ import annotations

from .base import ProviderInvoice, ProviderResult, ProviderStatusResult, ValidationResult
from ..invoicepilot.statuses import InvoicePilotStatus, ProviderName


class MockProvider:
    name = ProviderName.MOCK.value

    def validate_payload(self, invoice: ProviderInvoice) -> ValidationResult:
        errors = []
        if not invoice.invoice_number:
            errors.append("Le numéro de facture est obligatoire.")
        if invoice.amount_ttc is not None and invoice.amount_ttc < 0:
            errors.append("Le montant TTC doit être positif.")
        return ValidationResult(valid=not errors, errors=errors)

    def submit_invoice(self, invoice: ProviderInvoice) -> ProviderResult:
        validation = self.validate_payload(invoice)
        if not validation.valid:
            return ProviderResult(
                ok=False,
                provider_name=self.name,
                internal_status=InvoicePilotStatus.ERROR.value,
                user_message=validation.errors[0],
                technical_details={"errors": validation.errors},
            )
        external_id = invoice.external_invoice_id or f"mock-{invoice.id}"
        return ProviderResult(
            ok=True,
            provider_name=self.name,
            external_invoice_id=external_id,
            internal_status=InvoicePilotStatus.SUBMITTED.value,
            external_status="MOCK_SUBMITTED",
            user_message="Facture simulée sans appel externe.",
            technical_details={"mock": True},
        )

    def get_status(self, external_invoice_id: str) -> ProviderStatusResult:
        return ProviderStatusResult(
            provider_name=self.name,
            external_invoice_id=external_invoice_id,
            internal_status=InvoicePilotStatus.ACCEPTED.value,
            external_status="MOCK_ACCEPTED",
            raw_response={"mock": True},
        )

    def cancel_invoice(self, external_invoice_id: str) -> ProviderResult:
        return ProviderResult(
            ok=True,
            provider_name=self.name,
            external_invoice_id=external_invoice_id,
            internal_status=InvoicePilotStatus.ERROR.value,
            external_status="MOCK_CANCELLED",
            user_message="Facture simulée annulée.",
            technical_details={"mock": True},
        )
