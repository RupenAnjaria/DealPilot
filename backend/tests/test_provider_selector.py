from app.models.query import ParsedQuery
from app.services.provider_selector import DeterministicProviderSelector

ALL_PROVIDERS = ["nike", "amazon", "walmart", "ebay"]


def _select(**overrides):
    defaults = dict(raw_query="q")
    defaults.update(overrides)
    query = ParsedQuery(**defaults)
    return DeterministicProviderSelector().select(query, ALL_PROVIDERS)


def test_brand_specific_nike_query_prioritizes_nike_first() -> None:
    selections = _select(brand="Nike")
    assert [s.provider for s in selections] == ["nike", "amazon", "walmart", "ebay"]
    assert selections[0].priority == 1
    assert "Nike" in selections[0].reason
    assert "prioritizing" in selections[0].reason.lower()


def test_all_four_providers_considered_for_nike_query() -> None:
    selections = _select(brand="Nike", model="Pegasus 41", size="10")
    assert {s.provider for s in selections} == set(ALL_PROVIDERS)


def test_no_brand_still_considers_all_providers_with_marketplaces_first() -> None:
    selections = _select()
    assert [s.provider for s in selections] == ["amazon", "walmart", "ebay", "nike"]
    nike_selection = next(s for s in selections if s.provider == "nike")
    assert "no specific brand" in nike_selection.reason.lower()


def test_different_brand_excludes_single_brand_store() -> None:
    selections = _select(brand="Adidas")
    assert "nike" not in {s.provider for s in selections}
    assert {s.provider for s in selections} == {"amazon", "walmart", "ebay"}


def test_marketplace_reasons_mention_general_comparison() -> None:
    selections = _select(brand="Adidas")
    for selection in selections:
        assert "marketplace" in selection.reason.lower()


def test_priorities_are_sequential_starting_at_one() -> None:
    selections = _select(brand="Nike")
    assert [s.priority for s in selections] == [1, 2, 3, 4]


def test_respects_available_providers_subset() -> None:
    selections = DeterministicProviderSelector().select(
        ParsedQuery(raw_query="q", brand="Nike"), ["amazon", "ebay"]
    )
    assert {s.provider for s in selections} == {"amazon", "ebay"}
