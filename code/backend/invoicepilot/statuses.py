from __future__ import annotations

from enum import StrEnum


class InvoicePilotStatus(StrEnum):
    UPLOADED = "UPLOADED"
    EXTRACTED = "EXTRACTED"
    TO_VALIDATE = "TO_VALIDATE"
    READY_TO_SUBMIT = "READY_TO_SUBMIT"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PAID = "PAID"
    ERROR = "ERROR"


class InvoiceChannel(StrEnum):
    PUBLIC_SECTOR = "PUBLIC_SECTOR"
    B2B_PRIVATE = "B2B_PRIVATE"
    MOCK = "MOCK"


class ProviderName(StrEnum):
    CHORUS_PRO = "CHORUS_PRO"
    MOCK = "MOCK"
    FUTURE_PDP = "FUTURE_PDP"


class InvoiceEventType(StrEnum):
    INVOICE_UPLOADED = "INVOICE_UPLOADED"
    PDF_EXTRACTED = "PDF_EXTRACTED"
    PUBLIC_CUSTOMER_LINKED = "PUBLIC_CUSTOMER_LINKED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    VALIDATION_PASSED = "VALIDATION_PASSED"
    SUBMISSION_STARTED = "SUBMISSION_STARTED"
    SUBMISSION_SUCCESS = "SUBMISSION_SUCCESS"
    SUBMISSION_FAILED = "SUBMISSION_FAILED"
    STATUS_SYNCED = "STATUS_SYNCED"
    PAYMENT_STATUS_UPDATED = "PAYMENT_STATUS_UPDATED"


LEGACY_STATUS_TO_INVOICEPILOT = {
    "DRAFT_UPLOADED": InvoicePilotStatus.UPLOADED,
    "DRAFT_STRUCTURED": InvoicePilotStatus.EXTRACTED,
    "PENDING_HUMAN_REVIEW": InvoicePilotStatus.TO_VALIDATE,
    "READY_FOR_SUBMISSION": InvoicePilotStatus.READY_TO_SUBMIT,
    "SUBMISSION_REQUESTED": InvoicePilotStatus.SUBMITTED,
    "ATTACHMENTS_UPLOADED": InvoicePilotStatus.SUBMITTED,
    "SUBMITTED_TO_CHORUS": InvoicePilotStatus.SUBMITTED,
    "STATUS_SYNC_PENDING": InvoicePilotStatus.SUBMITTED,
    "REJECTED_BUSINESS": InvoicePilotStatus.REJECTED,
    "REJECTED_TECHNICAL": InvoicePilotStatus.ERROR,
    "ACCEPTED_BY_CHORUS": InvoicePilotStatus.ACCEPTED,
    "PAID": InvoicePilotStatus.PAID,
    "ARCHIVED": InvoicePilotStatus.ACCEPTED,
}


CHORUS_STATUS_TO_INVOICEPILOT = {
    "MISE_EN_PAIEMENT": InvoicePilotStatus.PAID,
    "MANDATEE": InvoicePilotStatus.ACCEPTED,
    "COMPTABILISEE": InvoicePilotStatus.ACCEPTED,
    "SERVICE_FAIT": InvoicePilotStatus.ACCEPTED,
    "VALIDEE_1": InvoicePilotStatus.ACCEPTED,
    "VALIDEE_2": InvoicePilotStatus.ACCEPTED,
    "PRISE_EN_COMPTE_MOE": InvoicePilotStatus.ACCEPTED,
    "PRISE_EN_COMPTE_MOA": InvoicePilotStatus.ACCEPTED,
    "PRISE_EN_COMPTE_DESTINATAIRE": InvoicePilotStatus.ACCEPTED,
    "DEPOSEE": InvoicePilotStatus.SUBMITTED,
    "EN_COURS_ACHEMINEMENT": InvoicePilotStatus.SUBMITTED,
    "MISE_A_DISPOSITION": InvoicePilotStatus.SUBMITTED,
    "REJETEE": InvoicePilotStatus.REJECTED,
    "REFUSEE_1": InvoicePilotStatus.REJECTED,
    "REFUSEE_2": InvoicePilotStatus.REJECTED,
    "REFUSEE_MOE": InvoicePilotStatus.REJECTED,
    "REFUSEE_MOA": InvoicePilotStatus.REJECTED,
    "REFUSEE_FOURNISSEUR": InvoicePilotStatus.REJECTED,
    "NON_CONFORME": InvoicePilotStatus.REJECTED,
    "ABANDONNEE": InvoicePilotStatus.ERROR,
    "SUPPRIMEE": InvoicePilotStatus.ERROR,
    "TECHNIQUE_INCONNU": InvoicePilotStatus.ERROR,
}


def normalize_invoicepilot_status(value: str | InvoicePilotStatus | None) -> InvoicePilotStatus:
    if isinstance(value, InvoicePilotStatus):
        return value
    normalized = (value or "").strip().upper()
    try:
        return InvoicePilotStatus(normalized)
    except ValueError:
        pass
    return LEGACY_STATUS_TO_INVOICEPILOT.get(normalized, InvoicePilotStatus.TO_VALIDATE)


def legacy_status_to_invoicepilot(status: str | None) -> InvoicePilotStatus:
    return normalize_invoicepilot_status(status)


def chorus_status_to_invoicepilot(status: str | None) -> InvoicePilotStatus:
    normalized = (status or "").strip().upper()
    if not normalized:
        return InvoicePilotStatus.SUBMITTED
    return CHORUS_STATUS_TO_INVOICEPILOT.get(normalized, InvoicePilotStatus.SUBMITTED)
