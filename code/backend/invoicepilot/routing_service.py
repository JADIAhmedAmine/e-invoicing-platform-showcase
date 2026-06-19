from __future__ import annotations

from ..providers import ChorusProProvider, FuturePDPProvider, InvoiceProvider, MockProvider
from .statuses import InvoiceChannel, ProviderName


class RoutingService:
    def __init__(self, providers: dict[str, InvoiceProvider] | None = None) -> None:
        self.providers = providers or {}

    def _provider(self, name: ProviderName) -> InvoiceProvider:
        key = name.value
        if key in self.providers:
            return self.providers[key]
        if name is ProviderName.CHORUS_PRO:
            provider = ChorusProProvider()
        elif name is ProviderName.FUTURE_PDP:
            provider = FuturePDPProvider()
        else:
            provider = MockProvider()
        self.providers[key] = provider
        return provider

    def choose_provider(
        self,
        *,
        channel: str | None,
        provider_name: str | None = None,
    ) -> InvoiceProvider:
        if provider_name:
            normalized = provider_name.strip().upper()
            if normalized == ProviderName.CHORUS_PRO.value:
                return self._provider(ProviderName.CHORUS_PRO)
            if normalized == ProviderName.FUTURE_PDP.value:
                return self._provider(ProviderName.FUTURE_PDP)
            return self._provider(ProviderName.MOCK)

        if (channel or "").strip().upper() == InvoiceChannel.PUBLIC_SECTOR.value:
            return self._provider(ProviderName.CHORUS_PRO)
        if (channel or "").strip().upper() == InvoiceChannel.B2B_PRIVATE.value:
            return self._provider(ProviderName.FUTURE_PDP)
        return self._provider(ProviderName.MOCK)
