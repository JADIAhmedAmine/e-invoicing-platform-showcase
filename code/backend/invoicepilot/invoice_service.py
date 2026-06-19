from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from ..db.entities import Invoice
from ..providers import ProviderError, ProviderInvoice
from .event_service import create_api_log, create_invoice_event
from .routing_service import RoutingService
from .statuses import InvoiceEventType, InvoicePilotStatus
from .validation_service import validate_invoice_for_submission


class InvoiceService:
    def __init__(self, routing_service: RoutingService | None = None) -> None:
        self.routing_service = routing_service or RoutingService()

    def validate_invoice(self, session: Session, invoice: Invoice) -> list[str]:
        errors = validate_invoice_for_submission(invoice)
        create_invoice_event(
            session,
            invoice_id=invoice.id,
            event_type=(
                InvoiceEventType.VALIDATION_FAILED.value
                if errors
                else InvoiceEventType.VALIDATION_PASSED.value
            ),
            old_status=invoice.status_internal,
            new_status=invoice.status_internal,
            message=errors[0] if errors else "Facture validée pour routage.",
            technical_details={"errors": errors} if errors else None,
        )
        return errors

    def submit_prepared_payload(
        self,
        session: Session,
        *,
        invoice: Invoice,
        payload: dict[str, Any],
        main_file: dict[str, Any] | None = None,
        attachments: list[dict[str, Any]] | None = None,
        provider_name: str | None = None,
    ) -> Invoice:
        provider = self.routing_service.choose_provider(
            channel=invoice.channel,
            provider_name=provider_name or invoice.provider_name,
        )
        old_status = invoice.status_internal
        invoice.provider_name = provider.name
        invoice.status_internal = InvoicePilotStatus.SUBMITTED.value
        create_invoice_event(
            session,
            invoice_id=invoice.id,
            event_type=InvoiceEventType.SUBMISSION_STARTED.value,
            old_status=old_status,
            new_status=invoice.status_internal,
            message=f"Soumission via {provider.name}.",
        )

        provider_invoice = ProviderInvoice(
            id=invoice.id,
            invoice_number=invoice.supplier_invoice_number,
            invoice_date=invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            amount_ht=invoice.total_ht,
            amount_tva=invoice.total_vat,
            amount_ttc=invoice.total_ttc,
            currency=invoice.currency_code,
            channel=invoice.channel,
            provider_name=provider.name,
            external_invoice_id=invoice.external_invoice_id,
            payload=payload,
            main_file=main_file,
            attachments=attachments or [],
        )

        try:
            result = provider.submit_invoice(provider_invoice)
        except ProviderError as error:
            invoice.status_internal = InvoicePilotStatus.ERROR.value
            for call in error.api_calls:
                create_api_log(
                    session,
                    invoice_id=invoice.id,
                    provider_name=error.provider_name,
                    endpoint=str(call.get("url") or call.get("label") or ""),
                    method=str(call.get("method") or "POST"),
                    request_payload=call.get("requestBody") if isinstance(call.get("requestBody"), dict) else None,
                    response_payload=call.get("responseBody"),
                    status_code=call.get("responseStatus") if isinstance(call.get("responseStatus"), int) else None,
                    error_message=error.technical_message,
                )
            create_invoice_event(
                session,
                invoice_id=invoice.id,
                event_type=InvoiceEventType.SUBMISSION_FAILED.value,
                old_status=old_status,
                new_status=invoice.status_internal,
                message=error.user_message,
                technical_details={"error": error.technical_message},
            )
            raise

        if not result.ok:
            invoice.status_internal = result.internal_status or InvoicePilotStatus.ERROR.value
            create_invoice_event(
                session,
                invoice_id=invoice.id,
                event_type=InvoiceEventType.SUBMISSION_FAILED.value,
                old_status=old_status,
                new_status=invoice.status_internal,
                message=result.user_message or "Soumission refusée par le provider.",
                technical_details=result.technical_details,
            )
            session.flush()
            return invoice

        invoice.provider_name = result.provider_name
        invoice.external_invoice_id = result.external_invoice_id
        invoice.chorus_invoice_number = result.external_invoice_id or invoice.chorus_invoice_number
        invoice.status_chorus = result.external_status or invoice.status_chorus
        invoice.status_internal = result.internal_status or InvoicePilotStatus.SUBMITTED.value
        invoice.submitted_at = datetime.now(timezone.utc)
        invoice.last_status_sync_at = invoice.submitted_at

        for call in result.api_calls:
            create_api_log(
                session,
                invoice_id=invoice.id,
                provider_name=result.provider_name,
                endpoint=str(call.get("url") or call.get("label") or ""),
                method=str(call.get("method") or "POST"),
                request_payload=call.get("requestBody") if isinstance(call.get("requestBody"), dict) else None,
                response_payload=call.get("responseBody"),
                status_code=call.get("responseStatus") if isinstance(call.get("responseStatus"), int) else None,
            )

        create_invoice_event(
            session,
            invoice_id=invoice.id,
            event_type=InvoiceEventType.SUBMISSION_SUCCESS.value,
            old_status=old_status,
            new_status=invoice.status_internal,
            message=result.user_message,
            technical_details=result.technical_details,
        )
        session.flush()
        return invoice
