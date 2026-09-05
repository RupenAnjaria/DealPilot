from abc import ABC, abstractmethod

from app.models.provider_selection import ProviderSelection
from app.models.query import ParsedQuery

# Providers that exclusively sell one brand's products (lowercase brand name).
# Everyone else is treated as a brand-agnostic marketplace.
OFFICIAL_STORE_BRANDS = {"nike": "nike"}

# Default marketplace search order when brand doesn't otherwise break the tie.
DEFAULT_MARKETPLACE_ORDER = ["amazon", "walmart", "ebay"]


class ProviderSelector(ABC):
    """Decides which available providers to search for a request, and in what order.

    Kept as an abstract interface so an AI-based (or AI-augmented) selector can later
    replace or wrap this logic without changing callers — only get_provider_selector()
    needs to change.
    """

    @abstractmethod
    def select(self, parsed_query: ParsedQuery, available_providers: list[str]) -> list[ProviderSelection]:
        """Return the providers to search, ordered by priority (index 0 = highest)."""
        raise NotImplementedError


class DeterministicProviderSelector(ProviderSelector):
    """Rule-based selection: prioritize a matching brand's official store, skip it otherwise."""

    def select(self, parsed_query: ParsedQuery, available_providers: list[str]) -> list[ProviderSelection]:
        query_brand = parsed_query.brand.lower() if parsed_query.brand else None

        candidates = []
        for provider in available_providers:
            official_brand = OFFICIAL_STORE_BRANDS.get(provider)
            # A single-brand store can't carry a different brand's products — drop it entirely.
            if official_brand is not None and query_brand is not None and query_brand != official_brand:
                continue
            candidates.append((provider, official_brand))

        def sort_key(candidate: tuple[str, str | None]) -> tuple[int, int, str]:
            provider, official_brand = candidate
            if official_brand is not None and official_brand == query_brand:
                return (0, 0, provider)  # matched official store: always searched first
            if official_brand is None:
                rank = DEFAULT_MARKETPLACE_ORDER.index(provider) if provider in DEFAULT_MARKETPLACE_ORDER else 99
                return (1, rank, provider)  # brand-agnostic marketplace
            return (2, 0, provider)  # official store, but no brand requested: lowest priority

        candidates.sort(key=sort_key)

        selections = []
        for priority, (provider, official_brand) in enumerate(candidates, start=1):
            if official_brand is not None and official_brand == query_brand:
                reason = (
                    f"Query specifies {parsed_query.brand} as the brand; "
                    f"prioritizing {provider.title()}'s official store."
                )
            elif official_brand is not None:
                reason = f"No specific brand requested; including {provider.title()}'s official store as a candidate."
            else:
                reason = "General marketplace; carries multiple brands and compares prices across sellers."
            selections.append(ProviderSelection(provider=provider, priority=priority, reason=reason))
        return selections


def get_provider_selector() -> ProviderSelector:
    """Swap point: return an AI-based/augmented selector here later without touching callers."""
    return DeterministicProviderSelector()
