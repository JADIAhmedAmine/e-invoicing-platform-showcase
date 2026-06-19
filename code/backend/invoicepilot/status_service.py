from __future__ import annotations

from .statuses import InvoicePilotStatus, chorus_status_to_invoicepilot, legacy_status_to_invoicepilot


def map_external_status(provider_name: str | None, external_status: str | None) -> InvoicePilotStatus:
    if (provider_name or "").upper() == "CHORUS_PRO":
        return chorus_status_to_invoicepilot(external_status)
    return legacy_status_to_invoicepilot(external_status)
