import json
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.models.product import ProviderListing
from app.models.query import ParsedQuery
from app.services.pricing import calculate_total_price

CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "catalog.json"
RETAILER_LISTINGS_PATH = Path(__file__).resolve().parents[2] / "data" / "retailer_listings.json"


@lru_cache(maxsize=1)
def load_catalog() -> list[dict[str, Any]]:
    """Canonical product identities, shared by the parser (brand/model recognition) and providers."""
    with CATALOG_PATH.open(encoding="utf-8") as f:
        return json.load(f)["products"]


@lru_cache(maxsize=1)
def load_retailer_listings() -> list[dict[str, Any]]:
    """Hand-authored mock inventory: one entry per (provider, canonical product)."""
    with RETAILER_LISTINGS_PATH.open(encoding="utf-8") as f:
        return json.load(f)["listings"]


@lru_cache(maxsize=1)
def _catalog_by_id() -> dict[str, dict[str, Any]]:
    return {entry["id"]: entry for entry in load_catalog()}


def _contains(haystack: str, needle: str) -> bool:
    return needle.strip().lower() in haystack.strip().lower()


def _matches_query(canonical: dict[str, Any], raw_listing: dict[str, Any], parsed_query: ParsedQuery) -> bool:
    """Whether a retailer's listing (joined with its canonical product) satisfies the search request."""
    # Every filter below is skipped when the corresponding field is None, so a query with no
    # identifying anchor at all (e.g. an unrecognized brand/product) would otherwise match
    # every single catalog entry. Require at least one anchor before considering anything a match.
    if not any([parsed_query.brand, parsed_query.model, parsed_query.sku, parsed_query.category]):
        return False
    if parsed_query.brand and canonical["brand"].lower() != parsed_query.brand.lower():
        return False
    if parsed_query.sku and (raw_listing.get("sku") or "").lower() != parsed_query.sku.lower():
        return False
    if parsed_query.model and not (
        _contains(canonical["model"], parsed_query.model) or _contains(parsed_query.model, canonical["model"])
    ):
        return False
    if parsed_query.category and not _contains(canonical["category"], parsed_query.category):
        return False
    if parsed_query.gender and canonical["gender"].lower() != parsed_query.gender.lower():
        return False
    if parsed_query.size and parsed_query.size.strip().lower() not in [
        s.lower() for s in raw_listing["sizes"]
    ]:
        return False
    if parsed_query.color and parsed_query.color.strip().lower() not in [
        c.lower() for c in raw_listing["colors"]
    ]:
        return False
    return True


class Provider(ABC):
    """Interface implemented by every (mock, for now) retailer provider."""

    name: str

    @abstractmethod
    def search(self, parsed_query: ParsedQuery) -> list[ProviderListing]:
        """Return normalized listings for this provider matching the parsed query."""
        raise NotImplementedError


def search_provider_inventory(provider: str, parsed_query: ParsedQuery) -> list[ProviderListing]:
    """Filter this provider's authored mock inventory against the search request.

    Every provider returns listings in the same normalized ProviderListing shape,
    with only the underlying data (title wording, price, SKU format, color naming,
    size availability, stock status) varying by retailer.
    """
    catalog_by_id = _catalog_by_id()
    listings: list[ProviderListing] = []
    for raw in load_retailer_listings():
        if raw["provider"] != provider:
            continue
        canonical = catalog_by_id[raw["canonical_id"]]
        if not _matches_query(canonical, raw, parsed_query):
            continue

        size = parsed_query.size or raw["sizes"][0]
        canonical_color = parsed_query.color or next(iter(raw["colors"]))
        price = raw["price"]
        shipping = raw["shipping"]
        total_price = calculate_total_price(price, shipping)
        if parsed_query.max_price is not None and total_price > parsed_query.max_price:
            continue

        listings.append(
            ProviderListing(
                listing_id=f"{provider}-{canonical['id']}",
                provider=provider,
                title=raw["title"],
                brand=canonical["brand"],
                model=canonical["model"],
                sku=raw.get("sku"),
                category=canonical["category"],
                gender=canonical["gender"],
                size=size,
                color=raw["colors"][canonical_color],
                price=price,
                shipping=shipping,
                total_price=total_price,
                currency="USD",
                availability=raw.get("availability", "in_stock"),
                product_url=f"https://{provider}.example.com/products/{canonical['id']}",
                official_store=raw.get("official_store", False),
                rating=raw.get("rating"),
            )
        )
    return listings

