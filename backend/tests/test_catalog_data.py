from app.services.providers.base import load_catalog, load_retailer_listings

VALID_AVAILABILITY = {"in_stock", "out_of_stock", "limited"}
VALID_PROVIDERS = {"nike", "amazon", "walmart", "ebay"}


def test_catalog_loads_and_is_non_empty() -> None:
    catalog = load_catalog()
    assert len(catalog) > 0


def test_catalog_entries_have_required_fields() -> None:
    required_fields = {"id", "brand", "model", "sku", "category", "gender", "sizes", "colors", "base_price"}
    for entry in load_catalog():
        assert required_fields.issubset(entry.keys())
        assert entry["sizes"], f"{entry['id']} must list at least one size"
        assert entry["colors"], f"{entry['id']} must list at least one color"
        assert entry["base_price"] > 0


def test_catalog_ids_are_unique() -> None:
    ids = [entry["id"] for entry in load_catalog()]
    assert len(ids) == len(set(ids))


def test_catalog_includes_the_requested_nike_models() -> None:
    models = {(entry["brand"], entry["model"]) for entry in load_catalog()}
    assert ("Nike", "Pegasus 41") in models
    assert ("Nike", "Air Max 270") in models
    assert ("Nike", "Air Force 1 '07") in models
    assert ("Nike", "Vomero 17") in models


def test_catalog_includes_deliberately_similar_product_names() -> None:
    """Near-duplicate names (same family, different model) must stay distinct products."""
    models_by_brand: dict[str, set[str]] = {}
    for entry in load_catalog():
        models_by_brand.setdefault(entry["brand"], set()).add(entry["model"])

    nike_models = models_by_brand["Nike"]
    assert {"Pegasus 41", "Pegasus 40"}.issubset(nike_models)
    assert {"Air Max 270", "Air Max 270 React"}.issubset(nike_models)
    assert {"Vomero 17", "Vomero 18"}.issubset(nike_models)


def test_retailer_listings_load_and_are_non_empty() -> None:
    listings = load_retailer_listings()
    assert len(listings) > 0


def test_retailer_listings_reference_known_catalog_products() -> None:
    catalog_ids = {entry["id"] for entry in load_catalog()}
    for listing in load_retailer_listings():
        assert listing["canonical_id"] in catalog_ids


def test_retailer_listings_have_required_fields_and_valid_values() -> None:
    required_fields = {
        "provider", "canonical_id", "title", "sku", "price", "shipping",
        "official_store", "availability", "rating", "sizes", "colors",
    }
    for listing in load_retailer_listings():
        assert required_fields.issubset(listing.keys())
        assert listing["provider"] in VALID_PROVIDERS
        assert listing["availability"] in VALID_AVAILABILITY
        assert listing["price"] > 0
        assert listing["shipping"] >= 0
        assert listing["sizes"], f"{listing['provider']}/{listing['canonical_id']} must list at least one size"
        assert listing["colors"], f"{listing['provider']}/{listing['canonical_id']} must list at least one color"


def test_only_nike_provider_listings_are_marked_official_store() -> None:
    for listing in load_retailer_listings():
        if listing["official_store"]:
            assert listing["provider"] == "nike"


def test_ebay_listings_never_carry_a_manufacturer_sku() -> None:
    ebay_listings = [listing for listing in load_retailer_listings() if listing["provider"] == "ebay"]
    assert ebay_listings
    assert all(listing["sku"] is None for listing in ebay_listings)


def test_same_product_has_multiple_retailers_with_varying_data() -> None:
    """At least one product must be sold by 3+ retailers with different titles/prices/shipping,
    proving DealPilot must normalize listings rather than compare identical strings."""
    listings_by_product: dict[str, list[dict]] = {}
    for listing in load_retailer_listings():
        listings_by_product.setdefault(listing["canonical_id"], []).append(listing)

    pegasus_41 = listings_by_product["nike-pegasus-41"]
    assert len(pegasus_41) >= 3

    titles = {listing["title"] for listing in pegasus_41}
    prices = {listing["price"] for listing in pegasus_41}
    shippings = {listing["shipping"] for listing in pegasus_41}
    assert len(titles) == len(pegasus_41), "each retailer must word the title differently"
    assert len(prices) > 1, "price must vary across retailers"
    assert len(shippings) > 1, "shipping must vary across retailers"


def test_retailer_listings_vary_color_naming_and_size_availability() -> None:
    """A single product's color labels and size lists should differ across retailers."""
    listings_by_product: dict[str, list[dict]] = {}
    for listing in load_retailer_listings():
        listings_by_product.setdefault(listing["canonical_id"], []).append(listing)

    pegasus_41 = listings_by_product["nike-pegasus-41"]
    color_labels = {listing["colors"]["black"] for listing in pegasus_41}
    size_sets = {tuple(listing["sizes"]) for listing in pegasus_41}
    assert len(color_labels) > 1, "retailers must describe the same color differently"
    assert len(size_sets) > 1, "retailers must carry different size subsets"


def test_retailer_listings_vary_sku_formatting() -> None:
    """The same manufacturer SKU should appear formatted differently across retailers."""
    listings_by_product: dict[str, list[dict]] = {}
    for listing in load_retailer_listings():
        listings_by_product.setdefault(listing["canonical_id"], []).append(listing)

    pegasus_41 = listings_by_product["nike-pegasus-41"]
    skus = {listing["sku"] for listing in pegasus_41 if listing["sku"]}
    assert len(skus) > 1, "SKU formatting must differ across retailers (e.g. dashes vs none)"


def test_dataset_includes_some_non_standard_availability() -> None:
    """Some listings must be out of stock or limited, so ranking can prove it excludes them."""
    statuses = {listing["availability"] for listing in load_retailer_listings()}
    assert "out_of_stock" in statuses
    assert "limited" in statuses
