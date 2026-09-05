from app.models.query import ParsedQuery
from app.services.providers.registry import get_providers


def _query(**overrides) -> ParsedQuery:
    defaults = dict(raw_query="Nike Pegasus 41 mens size 10 black under $200")
    defaults.update(overrides)
    return ParsedQuery(**defaults)


def test_registry_returns_all_four_providers() -> None:
    providers = get_providers()
    assert {p.name for p in providers} == {"nike", "amazon", "walmart", "ebay"}


def test_nike_provider_only_returns_nike_and_is_official() -> None:
    providers = get_providers()
    nike = next(p for p in providers if p.name == "nike")
    listings = nike.search(_query(brand="Adidas"))
    assert listings == []

    listings = nike.search(_query(brand="Nike", model="Pegasus 41", gender="men", size="10", color="black"))
    assert len(listings) == 1
    listing = listings[0]
    assert listing.official_store is True
    assert listing.shipping == 0.0
    assert listing.sku == "DV3853-001"
    assert listing.size == "10"
    assert listing.color == "Black"


def test_ebay_listings_never_include_sku() -> None:
    providers = get_providers()
    ebay = next(p for p in providers if p.name == "ebay")
    listings = ebay.search(_query(brand="Nike", model="Pegasus 41"))
    assert listings
    assert all(listing.sku is None for listing in listings)
    assert all(listing.official_store is False for listing in listings)


def test_amazon_provider_returns_marketplace_listing_not_official() -> None:
    providers = get_providers()
    amazon = next(p for p in providers if p.name == "amazon")
    listings = amazon.search(_query(brand="Nike", model="Pegasus 41", gender="men", size="10", color="black"))
    assert len(listings) == 1
    listing = listings[0]
    assert listing.provider == "amazon"
    assert listing.official_store is False
    assert listing.sku == "DV3853-001"
    assert listing.brand == "Nike"


def test_amazon_provider_carries_non_nike_brands() -> None:
    providers = get_providers()
    amazon = next(p for p in providers if p.name == "amazon")
    listings = amazon.search(_query(brand="Adidas", model="Ultraboost 22"))
    assert listings
    assert all(listing.brand == "Adidas" for listing in listings)


def test_walmart_provider_returns_marketplace_listing_not_official() -> None:
    providers = get_providers()
    walmart = next(p for p in providers if p.name == "walmart")
    listings = walmart.search(_query(brand="Nike", model="Pegasus 41", gender="men", size="10", color="black"))
    assert len(listings) == 1
    listing = listings[0]
    assert listing.provider == "walmart"
    assert listing.official_store is False


def test_walmart_provider_size_availability_differs_from_manufacturer() -> None:
    providers = get_providers()
    walmart = next(p for p in providers if p.name == "walmart")
    # Walmart's mock inventory carries a narrower size range than Nike's own store.
    listings = walmart.search(_query(brand="Nike", model="Pegasus 41", gender="men", size="12", color="black"))
    assert listings == []


def test_unrecognized_product_returns_no_listings_from_any_provider() -> None:
    # A query with no brand/model/sku/category anchor (e.g. an out-of-catalog product like
    # a camera) must not fall through to matching every unrelated item in the catalog.
    providers = get_providers()
    query = _query(raw_query="cannon camera sku 334455", brand=None, model=None, sku=None, category=None)
    all_listings = [listing for provider in providers for listing in provider.search(query)]
    assert all_listings == []


def test_all_providers_return_matching_listings_for_full_query() -> None:
    providers = get_providers()
    query = _query(brand="Nike", model="Pegasus 41", category="running shoes", gender="men", size="10", color="black")
    all_listings = [listing for provider in providers for listing in provider.search(query)]
    assert len(all_listings) == 4
    assert {listing.provider for listing in all_listings} == {"nike", "amazon", "walmart", "ebay"}
    for listing in all_listings:
        assert listing.total_price == round(listing.price + listing.shipping, 2)


def test_max_price_filters_out_expensive_listings() -> None:
    providers = get_providers()
    query = _query(brand="Adidas", model="Ultraboost 22", max_price=100.0)
    all_listings = [listing for provider in providers for listing in provider.search(query)]
    assert all_listings == []


def test_size_and_color_filter_out_non_matching_catalog_entries() -> None:
    providers = get_providers()
    nike = next(p for p in providers if p.name == "nike")
    listings = nike.search(_query(brand="Nike", model="Pegasus 41", size="99", color="black"))
    assert listings == []
