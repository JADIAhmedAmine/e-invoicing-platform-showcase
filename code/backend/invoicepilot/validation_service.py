from __future__ import annotations

from decimal import Decimal

from ..db.entities import Invoice


def _digits(value: str | None) -> str:
    return "".join(character for character in (value or "") if character.isdigit())


def validate_invoice_for_submission(invoice: Invoice) -> list[str]:
    errors = []
    if not invoice.supplier_invoice_number:
        errors.append("Le numéro de facture est obligatoire.")
    if invoice.total_ttc is None or invoice.total_ttc < Decimal("0"):
        errors.append("Le montant TTC doit être positif.")
    if invoice.channel == "PUBLIC_SECTOR" and invoice.public_customer_id is None:
        customer_siret = _digits(
            invoice.raw_payload.get("customer_siret") if invoice.raw_payload else None
        )
        if len(customer_siret) != 14:
            errors.append(
                "Le destinataire public doit être identifié "
                "(SIRET 14 chiffres ou liaison à l'annuaire Chorus) avant soumission."
            )
    return errors
