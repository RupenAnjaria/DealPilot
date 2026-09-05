from app.models.product import ProviderListing
from app.services import matcher
from app.services.matcher import MATCH_THRESHOLD, compare_listings, match_listings


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
        color="Black",
        price=110.0,
        shipping=0.0,
        total_price=110.0,
        product_url="https://example.com/product",
    )
    defaults.update(overrides)
    return ProviderListing(**defaults)


# --- compare_listings: pairwise scoring ------------------------------------------------


def test_exact_sku_match_is_conclusive() -> None:
    a = _listing(provider="nike", sku="DV3853-001")
    b = _listing(provider="amazon", sku="DV3853-001", title="Nike Men's Air Zoom Pegasus 41 Running Shoes")
    result = compare_listings(a, b)
    assert result.score == 1.0
    assert result.is_match is True
    assert any("SKU" in line for line in result.explanation)


def test_sku_formatting_difference_still_matches() -> None:
    # Walmart formats the same manufacturer SKU without the dash.
    a = _listing(provider="nike", sku="DV3853-001")
    b = _listing(provider="walmart", sku="DV3853001")
    result = compare_listings(a, b)
    assert result.score == 1.0
    assert result.is_match is True


def test_conflicting_sku_forces_zero_score() -> None:
    a = _listing(provider="nike", sku="DV3853-001", model="Pegasus 41")
    b = _listing(provider="nike", sku="DV3853-100", model="Pegasus 40", title="Nike Pegasus 40")
    result = compare_listings(a, b)
    assert result.score == 0.0
    assert result.is_match is False
    assert any("Different SKUs" in line for line in result.explanation)


def test_brand_conflict_vetoes_match_even_without_sku() -> None:
    a = _listing(sku=None, brand="Nike")
    b = _listing(sku=None, brand="Adidas", model="Ultraboost 22", title="Adidas Ultraboost 22")
    result = compare_listings(a, b)
    assert result.score == 0.0
    assert result.is_match is False
    assert any("Brand differs" in line for line in result.explanation)


def test_similar_model_names_do_not_get_conflated() -> None:
    """'Pegasus 41' and 'Pegasus 40' are deliberately similar names but different products."""
    a = _listing(sku=None, model="Pegasus 41", title="Nike Pegasus 41")
    b = _listing(sku=None, model="Pegasus 40", title="Nike Pegasus 40")
    result = compare_listings(a, b)
    assert result.score == 0.0
    assert result.is_match is False
    assert any("Model differs" in line for line in result.explanation)


def test_gender_conflict_vetoes_match_without_sku() -> None:
    a = _listing(sku=None, gender="men")
    b = _listing(sku=None, gender="women")
    result = compare_listings(a, b)
    assert result.score == 0.0
    assert result.is_match is False
    assert any("Gender differs" in line for line in result.explanation)


def test_size_difference_does_not_veto_a_match_without_sku() -> None:
    """Query-time filtering already guarantees size agreement when the user asked for one;
    a differing *default* size (when they didn't) must not fragment the same product."""
    a = _listing(sku=None, size="10")
    b = _listing(sku=None, size="11")
    result = compare_listings(a, b)
    assert result.is_match is True
    assert any("Size differs" in line for line in result.explanation)


def test_title_wording_variation_does_not_block_a_match() -> None:
    """Same structured product, worded very differently by three retailers."""
    a = _listing(sku=None, title="Nike Pegasus 41")
    b = _listing(sku=None, title="Nike Men's Pegasus 41 Running Shoe")
    c = _listing(sku=None, title="Nike Air Zoom Pegasus 41")

    for other in (b, c):
        result = compare_listings(a, other)
        assert result.is_match is True, result.explanation
        assert any("Title similarity" in line for line in result.explanation)


def test_color_naming_variation_does_not_block_a_match() -> None:
    """Retailers describe the same color differently ('Black' vs 'Black/White')."""
    a = _listing(sku=None, color="Black")
    b = _listing(sku=None, color="Black/White")
    result = compare_listings(a, b)
    assert result.is_match is True
    assert any("Color similarity" in line for line in result.explanation)


def test_genuinely_different_color_lowers_score_but_is_not_a_hard_veto() -> None:
    same_color = compare_listings(_listing(sku=None, color="Black"), _listing(sku=None, color="Black"))
    different_color = compare_listings(_listing(sku=None, color="Black"), _listing(sku=None, color="Red"))
    assert different_color.score < same_color.score
    assert different_color.is_match is True  # color is the lowest-priority signal, not a critical field


def test_ambiguous_listing_with_only_weak_supporting_signals_is_not_confidently_matched() -> None:
    """Deliberately ambiguous: no brand/model/gender/size to compare, only a weak
    color/title resemblance. The engine should stay conservative rather than guess."""
    a = _listing(
        sku=None, brand=None, model=None, gender=None, size=None,
        color="Grey", title="Running Shoe Model 41",
    )
    b = _listing(
        sku=None, brand=None, model=None, gender=None, size=None,
        color="Charcoal", title="Trail Runner 41 Shoe",
    )
    result = compare_listings(a, b)
    assert result.score < MATCH_THRESHOLD
    assert result.is_match is False


def test_unknown_fields_are_not_counted_against_the_score() -> None:
    """A field missing on one side is skipped, not treated as a conflict."""
    a = _listing(sku=None, gender="men")
    b = _listing(sku=None, gender=None)
    result = compare_listings(a, b)
    assert any("Gender unknown" in line for line in result.explanation)
    assert result.is_match is True


# --- match_listings: grouping across providers -----------------------------------------


def test_grouping_merges_via_sku_despite_formatting_differences() -> None:
    nike = _listing(listing_id="nike-1", provider="nike", sku="DV3853-001", title="Nike Pegasus 41")
    amazon = _listing(
        listing_id="amazon-1", provider="amazon", sku="DV3853-001",
        title="Nike Men's Air Zoom Pegasus 41 Running Shoes",
    )
    walmart = _listing(
        listing_id="walmart-1", provider="walmart", sku="DV3853001", title="Nike Air Zoom Pegasus 41 (Men's)"
    )
    groups = match_listings([nike, amazon, walmart])
    assert len(groups) == 1
    assert len(groups[0].listings) == 3
    assert groups[0].match_confidence == 1.0
    assert groups[0].match_method == "deterministic"


def test_grouping_merges_sku_less_listing_via_structured_fields_and_title() -> None:
    nike = _listing(listing_id="nike-1", provider="nike", sku="DV3853-001", title="Nike Pegasus 41")
    ebay = _listing(
        listing_id="ebay-1", provider="ebay", sku=None,
        title="Nike Pegasus 41 Running Shoes Men's - New With Box",
    )
    groups = match_listings([nike, ebay])
    assert len(groups) == 1
    assert len(groups[0].listings) == 2


def test_grouping_keeps_similar_model_names_in_separate_groups() -> None:
    pegasus_41 = _listing(listing_id="nike-1", sku="DV3853-001", model="Pegasus 41", title="Nike Pegasus 41")
    pegasus_40 = _listing(listing_id="nike-2", sku="DV3853-100", model="Pegasus 40", title="Nike Pegasus 40")
    groups = match_listings([pegasus_41, pegasus_40])
    assert len(groups) == 2


def test_grouping_keeps_different_brands_in_separate_groups() -> None:
    nike_shoe = _listing(listing_id="nike-1")
    adidas_shoe = _listing(
        listing_id="amazon-1", provider="amazon", brand="Adidas", model="Ultraboost 22",
        sku="GZ0127", title="Adidas Ultraboost 22",
    )
    groups = match_listings([nike_shoe, adidas_shoe])
    assert len(groups) == 2


def test_grouping_keeps_gender_variants_separate_even_with_shared_model_text() -> None:
    # Men's and women's Pegasus 41 share model text but have distinct manufacturer SKUs.
    mens = _listing(listing_id="nike-mens", sku="DV3853-001", gender="men")
    womens = _listing(listing_id="amazon-womens", provider="amazon", sku="DV3854-001", gender="women")
    groups = match_listings([mens, womens])
    assert len(groups) == 2


def test_group_confidence_reflects_the_weakest_pairwise_match_in_the_group() -> None:
    nike = _listing(listing_id="nike-1", sku="DV3853-001")
    ebay = _listing(listing_id="ebay-1", sku=None, title="Nike Men's Pegasus 41 Running Shoe")
    groups = match_listings([nike, ebay])
    assert len(groups) == 1
    assert 0.0 < groups[0].match_confidence < 1.0


def test_matcher_module_still_exposes_fuzz_for_backwards_compatibility() -> None:
    assert matcher.fuzz is not None


# --- AI gray-zone tie-break --------------------------------------------------------------


def _ambiguous_pair() -> tuple[ProviderListing, ProviderListing]:
    """Same brand/model/gender but differs enough on size/color/title to land in the
    deterministic gray zone (score ~0.73, just below MATCH_THRESHOLD) without AI."""
    a = _listing(sku=None)
    b = _listing(
        listing_id="listing-2",
        sku=None,
        size="11",
        color="Crimson",
        title="Totally Unrelated Product Title Xyzzy",
    )
    return a, b


def test_ambiguous_score_stays_deterministic_without_ai() -> None:
    a, b = _ambiguous_pair()
    result = compare_listings(a, b)
    assert MATCH_THRESHOLD > result.score >= 0.55
    assert result.is_match is False
    assert result.method == "deterministic"


def test_ambiguous_score_uses_ai_tiebreak_when_configured(monkeypatch) -> None:
    class _FakeClient:
        def complete_json(self, system_prompt: str, user_prompt: str):
            return {"same_product": True}

    monkeypatch.setattr(matcher, "get_ai_client", lambda: _FakeClient())

    a, b = _ambiguous_pair()
    result = compare_listings(a, b)
    assert result.is_match is True
    assert result.method == "ai"
    assert any("AI judged" in line for line in result.explanation)


def test_ai_tiebreak_falls_back_when_response_fails_validation(monkeypatch) -> None:
    class _FakeClient:
        def complete_json(self, system_prompt: str, user_prompt: str):
            return {}  # missing required "same_product" key

    monkeypatch.setattr(matcher, "get_ai_client", lambda: _FakeClient())

    a, b = _ambiguous_pair()
    result = compare_listings(a, b)
    assert result.method == "deterministic"
    assert result.is_match is False


def test_ai_tiebreak_falls_back_when_client_raises(monkeypatch) -> None:
    class _RaisingClient:
        def complete_json(self, system_prompt: str, user_prompt: str):
            raise RuntimeError("simulated AI outage")

    monkeypatch.setattr(matcher, "get_ai_client", lambda: _RaisingClient())

    a, b = _ambiguous_pair()
    result = compare_listings(a, b)
    assert result.method == "deterministic"
    assert result.is_match is False


def test_ai_tiebreak_never_triggers_outside_the_gray_zone(monkeypatch) -> None:
    """A clear non-match (e.g. conflicting brand) must never even ask AI."""
    calls = []

    class _FakeClient:
        def complete_json(self, system_prompt: str, user_prompt: str):
            calls.append(1)
            return {"same_product": True}

    monkeypatch.setattr(matcher, "get_ai_client", lambda: _FakeClient())

    a = _listing(sku=None, brand="Nike")
    b = _listing(sku=None, brand="Adidas", model="Ultraboost 22", title="Adidas Ultraboost 22")
    result = compare_listings(a, b)
    assert result.is_match is False
    assert calls == []


def test_group_match_method_reflects_ai_tiebreak(monkeypatch) -> None:
    class _FakeClient:
        def complete_json(self, system_prompt: str, user_prompt: str):
            return {"same_product": True}

    monkeypatch.setattr(matcher, "get_ai_client", lambda: _FakeClient())

    a, b = _ambiguous_pair()
    groups = match_listings([a, b])
    assert len(groups) == 1
    assert groups[0].match_method == "ai"

