from app.models.product import ProductGroup, ProviderListing
from app.models.query import ParsedQuery
from app.services import ranking


def _listing(**overrides) -> ProviderListing:
    defaults = dict(
        listing_id="listing-1",
        provider="nike",
        title="Nike Pegasus 41",
        brand="Nike",
        model="Pegasus 41",
        sku="DV3853-001",
        category="running shoes",
        gender="men",
        size="10",
        color="black",
        price=130.0,
        shipping=0.0,
        total_price=130.0,
        product_url="https://example.com/product",
        official_store=False,
    )
    defaults.update(overrides)
    return ProviderListing(**defaults)


def _group(*listings: ProviderListing) -> ProductGroup:
    return ProductGroup(
        group_id="group-1",
        canonical_title="Nike Pegasus 41",
        listings=list(listings),
        match_confidence=1.0,
    )


def test_no_listings_returns_empty_decision_facts() -> None:
    result = ranking.rank_products([], ParsedQuery(raw_query="nonexistent product"))
    assert result.cheapest_listing_id is None
    assert result.decision_facts.cheapest_total is None


def test_cheapest_is_lowest_total_price() -> None:
    cheap = _listing(listing_id="cheap", total_price=100.0)
    pricey = _listing(listing_id="pricey", total_price=150.0)
    result = ranking.rank_products([_group(cheap, pricey)], ParsedQuery(raw_query="q"))
    assert result.cheapest_listing_id == "cheap"
    assert result.decision_facts.cheapest_total == 100.0


def test_official_listing_identified_independently_of_cheapest() -> None:
    official = _listing(listing_id="official", total_price=140.0, official_store=True)
    cheaper_third_party = _listing(listing_id="third-party", total_price=100.0, official_store=False)
    result = ranking.rank_products([_group(official, cheaper_third_party)], ParsedQuery(raw_query="q"))
    assert result.cheapest_listing_id == "third-party"
    assert result.official_listing_id == "official"


def test_no_official_store_present_leaves_official_none() -> None:
    listing = _listing(official_store=False)
    result = ranking.rank_products([_group(listing)], ParsedQuery(raw_query="q"))
    assert result.official_listing_id is None
    assert result.decision_facts.official_total is None


def test_best_deal_prefers_official_within_small_margin() -> None:
    # Official is only slightly pricier than the cheapest third-party option;
    # the official-store bonus should tip the "best deal" pick to it.
    official = _listing(listing_id="official", total_price=101.0, official_store=True, shipping=0.0)
    third_party = _listing(listing_id="third-party", total_price=100.0, official_store=False, shipping=6.99)
    result = ranking.rank_products([_group(official, third_party)], ParsedQuery(raw_query="q"))
    assert result.cheapest_listing_id == "third-party"
    assert result.best_deal_listing_id == "official"
    assert result.decision_facts.price_delta_vs_cheapest == 1.0


def test_cheapest_is_also_best_deal_leaves_reason_none() -> None:
    only = _listing(listing_id="only", total_price=100.0)
    result = ranking.rank_products([_group(only)], ParsedQuery(raw_query="q"))
    assert result.cheapest_listing_id == result.best_deal_listing_id == "only"
    assert result.decision_facts.best_deal_reason is None


def test_attributes_matched_reflects_parsed_query_fields() -> None:
    result = ranking.rank_products(
        [_group(_listing())],
        ParsedQuery(raw_query="q", brand="Nike", size="10", max_price=200),
    )
    assert set(result.decision_facts.attributes_matched) == {"brand", "size"}


def test_cheapest_item_price_can_differ_from_cheapest_delivered() -> None:
    # Lower sticker price but expensive shipping pushes its *delivered* total above the other.
    cheap_item_expensive_shipping = _listing(listing_id="cheap-item", price=90.0, shipping=20.0, total_price=110.0)
    pricier_item_free_shipping = _listing(listing_id="free-ship", price=100.0, shipping=0.0, total_price=100.0)
    result = ranking.rank_products(
        [_group(cheap_item_expensive_shipping, pricier_item_free_shipping)], ParsedQuery(raw_query="q")
    )
    assert result.decision_facts.cheapest_item_listing_id == "cheap-item"
    assert result.decision_facts.cheapest_item_price == 90.0
    assert result.decision_facts.cheapest_listing_id == "free-ship"
    assert result.decision_facts.cheapest_total == 100.0


def test_out_of_stock_listing_is_excluded_entirely() -> None:
    in_stock = _listing(listing_id="in-stock", total_price=120.0, availability="in_stock")
    out_of_stock = _listing(listing_id="sold-out", total_price=90.0, availability="out_of_stock")
    result = ranking.rank_products([_group(in_stock, out_of_stock)], ParsedQuery(raw_query="q"))
    assert result.cheapest_listing_id == "in-stock"


def test_limited_availability_is_included_but_deprioritized_for_best_deal() -> None:
    # Cheaper but limited stock; a fully in-stock option that's only slightly pricier
    # should still win "best overall deal" thanks to the availability penalty.
    limited = _listing(listing_id="limited", total_price=100.0, availability="limited")
    in_stock = _listing(listing_id="plentiful", total_price=101.5, availability="in_stock")
    result = ranking.rank_products([_group(limited, in_stock)], ParsedQuery(raw_query="q"))
    assert result.cheapest_listing_id == "limited"  # still the cheapest delivered price
    assert result.best_deal_listing_id == "plentiful"  # but not the best overall deal
    assert result.decision_facts.best_deal_reason == "better stock availability than the cheapest option"


def test_low_match_confidence_deprioritizes_a_group_for_best_deal() -> None:
    confident_group = _group(_listing(listing_id="confident", total_price=101.0))
    confident_group.match_confidence = 1.0
    shaky_group = _group(_listing(listing_id="shaky", total_price=100.0))
    shaky_group.match_confidence = 0.5  # matched via weak signals, not a manufacturer SKU

    result = ranking.rank_products([confident_group, shaky_group], ParsedQuery(raw_query="q"))
    assert result.cheapest_listing_id == "shaky"  # still the cheapest delivered price
    assert result.best_deal_listing_id == "confident"  # but the shakier match isn't the best deal
    assert result.decision_facts.best_deal_reason == "a more confidently matched listing"
