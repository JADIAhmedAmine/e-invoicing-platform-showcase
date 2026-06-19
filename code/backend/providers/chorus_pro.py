from __future__ import annotations

from typing import Any

from .base import (
    ProviderError,
    ProviderInvoice,
    ProviderResult,
    ProviderStatusResult,
    ValidationResult,
)
from ..client import ChorusApiError, ChorusClient
from ..config import ChorusSettings, load_chorus_settings
from ..invoicepilot.statuses import (
    InvoicePilotStatus,
    ProviderName,
    chorus_status_to_invoicepilot,
)
from ..service import ChorusSubmissionService


def _extract_external_id(response: Any) -> str | None:
    if not isinstance(response, dict):
        return None
    for key in (
        "invoiceId",
        "numeroFactureChorus",
        "identifiantFactureCPP",
        "numeroDemandePaiement",
        "idFacture",
        "id",
    ):
        value = response.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, int):
            return str(value)
    return None


def _extract_external_status(response: Any) -> str | None:
    if not isinstance(response, dict):
        return None
    for key in ("statutCourant", "statutFacture", "statut", "libelleStatutCourant"):
        value = response.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "DEPOSEE"


def _user_message_from_chorus_error(error: Exception) -> str:
    message = str(error)
    normalized = message.lower()
    if "codedestinataire" in normalized or "destinataire" in normalized:
        return (
            "Le destinataire public n'est pas correctement identifié. "
            "Veuillez vérifier le SIRET ou le service exécutant."
        )
    if "idfournisseur" in normalized or "fournisseur" in normalized:
        return (
            "La structure fournisseur Chorus Pro n'est pas correctement configurée. "
            "Veuillez vérifier les identifiants fournisseur."
        )
    if "token" in normalized or "oauth" in normalized:
        return "La connexion PISTE a échoué. Veuillez vérifier les identifiants techniques."
    return "La soumission Chorus Pro a échoué. Veuillez corriger la facture ou réessayer."


class ChorusProProvider:
    name = ProviderName.CHORUS_PRO.value

    def __init__(
        self,
        settings: ChorusSettings | None = None,
        *,
        service: ChorusSubmissionService | None = None,
        client: ChorusClient | None = None,
    ) -> None:
        self.settings = settings or load_chorus_settings()
        self.client = client or (service.client if service is not None else ChorusClient(self.settings))
        self.service = service or ChorusSubmissionService(self.settings, self.client)

    def validate_payload(self, invoice: ProviderInvoice) -> ValidationResult:
        errors = []
        if not invoice.payload:
            errors.append("Le payload Chorus Pro est obligatoire pour la soumission.")
        if not invoice.invoice_number:
            errors.append("Le numéro de facture est obligatoire.")
        if invoice.payload and not invoice.payload.get("destinataire"):
            errors.append("Le destinataire Chorus Pro est obligatoire.")
        if invoice.payload and not invoice.payload.get("fournisseur"):
            errors.append("Le fournisseur Chorus Pro est obligatoire.")
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

        try:
            result = self.service.submit_prepared_payload(
                invoice.payload or {},
                main_file=invoice.main_file,
                attachments=invoice.attachments,
            )
        except (ChorusApiError, ValueError, RuntimeError) as error:
            raise ProviderError(
                _user_message_from_chorus_error(error),
                provider_name=self.name,
                technical_message=str(error),
                api_calls=list(self.client.api_calls),
            ) from error

        external_id = _extract_external_id(result.get("response")) or invoice.external_invoice_id
        external_status = _extract_external_status(result.get("response"))
        return ProviderResult(
            ok=True,
            provider_name=self.name,
            external_invoice_id=external_id,
            internal_status=chorus_status_to_invoicepilot(external_status).value,
            external_status=external_status,
            user_message="Facture transmise à Chorus Pro.",
            technical_details={
                "payload": result.get("payload"),
                "response": result.get("response"),
                "uploadedFiles": result.get("uploadedFiles", []),
            },
            api_calls=list(result.get("apiCalls") or []),
        )

    def get_status(self, external_invoice_id: str) -> ProviderStatusResult:
        return ProviderStatusResult(
            provider_name=self.name,
            external_invoice_id=external_invoice_id,
            internal_status=InvoicePilotStatus.SUBMITTED.value,
            external_status=None,
            raw_response={"todo": "Use supplier invoice search/detail endpoint for status sync."},
        )

    def cancel_invoice(self, external_invoice_id: str) -> ProviderResult:
        return ProviderResult(
            ok=False,
            provider_name=self.name,
            external_invoice_id=external_invoice_id,
            internal_status=InvoicePilotStatus.ERROR.value,
            user_message="L'annulation Chorus Pro n'est pas encore branchée.",
            technical_details={"todo": "Implement Chorus Pro cancellation if API contract supports it."},
        )
