from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass(slots=True)
class ProviderInvoice:
    id: str
    invoice_number: str
    invoice_date: str | None = None
    supplier_siret: str | None = None
    customer_siret: str | None = None
    customer_name: str | None = None
    amount_ht: Decimal | None = None
    amount_tva: Decimal | None = None
    amount_ttc: Decimal | None = None
    currency: str = "EUR"
    channel: str = "PUBLIC_SECTOR"
    provider_name: str | None = None
    external_invoice_id: str | None = None
    payload: dict[str, Any] | None = None
    main_file: dict[str, Any] | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)
    pdf_path: Path | None = None


@dataclass(slots=True)
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProviderResult:
    ok: bool
    provider_name: str
    external_invoice_id: str | None = None
    internal_status: str | None = None
    external_status: str | None = None
    user_message: str | None = None
    technical_details: dict[str, Any] = field(default_factory=dict)
    api_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class ProviderStatusResult:
    provider_name: str
    external_invoice_id: str
    internal_status: str
    external_status: str | None = None
    raw_response: dict[str, Any] | None = None


class ProviderError(RuntimeError):
    def __init__(
        self,
        user_message: str,
        *,
        provider_name: str,
        technical_message: str | None = None,
        api_calls: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(technical_message or user_message)
        self.user_message = user_message
        self.provider_name = provider_name
        self.technical_message = technical_message or user_message
        self.api_calls = list(api_calls or [])


@runtime_checkable
class InvoiceProvider(Protocol):
    name: str

    def validate_payload(self, invoice: ProviderInvoice) -> ValidationResult:
        ...

    def submit_invoice(self, invoice: ProviderInvoice) -> ProviderResult:
        ...

    def get_status(self, external_invoice_id: str) -> ProviderStatusResult:
        ...

    def cancel_invoice(self, external_invoice_id: str) -> ProviderResult:
        ...
