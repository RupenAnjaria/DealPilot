import pytest
from pydantic import ValidationError

from app.models.product import DecisionFacts, ProductGroup, ProviderListing, RankingResult, SearchResponse
from app.models.query import ParsedQuery


def _sample_listing(listing_id: str, price: float, shipping: float) -> ProviderListing:
    return ProviderListing(
        listing_id=listing_id,
        provider="nike",
        title="Nike Pegasus 41",
        brand="Nike",
        model="Pegasus 41",
        sku="DV3853-001",
        category="running shoes",
        gender="men",
        size="10",
        color="black",
        price=price,
        shipping=shipping,
        total_price=price + shipping,
        product_url="https://example.com/product",
        official_store=True,
    )


def test_parsed_query_defaults() -> None:
    parsed = ParsedQuery(raw_query="Nike Pegasus 41 mens size 10 black under $120")
    assert parsed.brand is None
    assert parsed.parse_method == "rule_based"
    assert parsed.keywords == []


def test_parsed_query_accepts_keywords() -> None:
    parsed = ParsedQuery(raw_query="comfy trail running shoes", keywords=["comfy", "trail"])
    assert parsed.keywords == ["comfy", "trail"]


def test_parsed_query_rejects_non_positive_max_price() -> None:
    with pytest.raises(ValidationError):
        ParsedQuery(raw_query="q", max_price=0)


def test_provider_listing_defaults() -> None:
    listing = _sample_listing("nike-1", 110.0, 0.0)
    assert listing.currency == "USD"
    assert listing.availability == "in_stock"
    assert listing.match_confidence == 1.0


def test_provider_listing_rejects_negative_price() -> None:
    with pytest.raises(ValidationError):
        _sample_listing("nike-1", -10.0, 0.0)


def test_provider_listing_rejects_out_of_range_match_confidence() -> None:
    with pytest.raises(ValidationError):
        ProviderListing(
            listing_id="nike-1",
            provider="nike",
            title="Nike Pegasus 41",
            price=110.0,
            shipping=0.0,
            total_price=110.0,
            product_url="https://example.com/product",
            match_confidence=1.5,
        )


def test_provider_listing_rejects_invalid_currency() -> None:
    with pytest.raises(ValidationError):
        ProviderListing(
            listing_id="nike-1",
            provider="nike",
            title="Nike Pegasus 41",
            price=110.0,
            shipping=0.0,
            total_price=110.0,
            product_url="https://example.com/product",
            currency="US",
        )


def test_provider_listing_accepts_out_of_stock_availability() -> None:
    listing = ProviderListing(
        listing_id="nike-1",
        provider="nike",
        title="Nike Pegasus 41",
        price=110.0,
        shipping=0.0,
        total_price=110.0,
        product_url="https://example.com/product",
        availability="out_of_stock",
    )
    assert listing.availability == "out_of_stock"


def test_search_response_round_trip() -> None:
    listing = _sample_listing("nike-1", 110.0, 0.0)
    group = ProductGroup(
        group_id="group-1",
        canonical_title="Nike Pegasus 41",
        listings=[listing],
        match_confidence=1.0,
    )
    facts = DecisionFacts(
        cheapest_listing_id=listing.listing_id,
        cheapest_total=listing.total_price,
        best_deal_listing_id=listing.listing_id,
        best_deal_total=listing.total_price,
        official_listing_id=listing.listing_id,
        official_total=listing.total_price,
        price_delta_vs_cheapest=0.0,
        attributes_matched=["size", "color"],
    )
    ranking = RankingResult(
        cheapest_listing_id=listing.listing_id,
        best_deal_listing_id=listing.listing_id,
        official_listing_id=listing.listing_id,
        decision_facts=facts,
        explanation="Nike's own store has the lowest total delivered price.",
    )
    response = SearchResponse(
        parsed_query=ParsedQuery(raw_query="Nike Pegasus 41 mens size 10 black under $120", brand="Nike"),
        provider_selection=[{"provider": "nike", "priority": 1, "reason": "Query specifies Nike as the brand."}],
        providers_searched=["nike"],
        groups=[group],
        ranking=ranking,
    )

    assert response.groups[0].listings[0].total_price == 110.0
    # Round-trip through JSON to make sure the schema is serializable for the API layer.
    restored = SearchResponse.model_validate_json(response.model_dump_json())
    assert restored == response
