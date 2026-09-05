from typing import List, Literal, Optional

from pydantic import BaseModel, field_validator

from app.models.provider_selection import ProviderSelection
from app.models.query import ParsedQuery

Availability = Literal["in_stock", "out_of_stock", "limited"]


class ProviderListing(BaseModel):
    """A single normalized deal result from one retailer provider.

    Every provider implementation must return listings in this exact shape so the
    matcher/ranking/explainer layers never need to know which retailer a listing came from.
    """

    listing_id: str
    provider: str
    title: str
    brand: Optional[str] = None
    model: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    gender: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    price: float
    shipping: float
    total_price: float
    currency: str = "USD"
    availability: Availability = "in_stock"
    product_url: str
    official_store: bool = False
    # Confidence that this listing matches the search request that produced it (0-1),
    # distinct from ProductGroup.match_confidence (cross-provider grouping confidence).
    match_confidence: float = 1.0
    rating: Optional[float] = None

    @field_validator("price", "shipping", "total_price")
    @classmethod
    def _non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("must be >= 0")
        return value

    @field_validator("match_confidence")
    @classmethod
    def _confidence_in_range(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("match_confidence must be between 0 and 1")
        return value

    @field_validator("currency")
    @classmethod
    def _currency_is_iso_code(cls, value: str) -> str:
        if len(value) != 3 or not value.isalpha():
            raise ValueError("currency must be a 3-letter ISO 4217 code, e.g. USD")
        return value.upper()


class ProductGroup(BaseModel):
    """Listings from different providers identified as the same underlying product."""

    group_id: str
    canonical_title: str
    listings: List[ProviderListing]
    match_confidence: float
    # How the listings in this group were matched together.
    match_method: Literal["deterministic", "ai"] = "deterministic"


class DecisionFacts(BaseModel):
    """Verified numeric facts ranking is based on; explanations must only restate these."""

    # Lowest raw item price (before shipping), which may differ from the cheapest delivered.
    cheapest_item_listing_id: Optional[str] = None
    cheapest_item_price: Optional[float] = None
    cheapest_listing_id: Optional[str] = None
    cheapest_total: Optional[float] = None
    best_deal_listing_id: Optional[str] = None
    best_deal_total: Optional[float] = None
    # Why best_deal differs from cheapest_delivered (None when they're the same listing).
    best_deal_reason: Optional[str] = None
    official_listing_id: Optional[str] = None
    official_total: Optional[float] = None
    price_delta_vs_cheapest: Optional[float] = None
    shipping_included: bool = True
    attributes_matched: List[str] = []


class RankingResult(BaseModel):
    """Ranking output: distinct cheapest/best-deal/official picks plus supporting facts."""

    cheapest_listing_id: Optional[str] = None
    best_deal_listing_id: Optional[str] = None
    official_listing_id: Optional[str] = None
    decision_facts: DecisionFacts
    explanation: str


class SearchResponse(BaseModel):
    """Top-level response returned by POST /api/search."""

    parsed_query: ParsedQuery
    provider_selection: List[ProviderSelection]
    providers_searched: List[str]
    groups: List[ProductGroup]
    ranking: RankingResult
