from app.models.product import DecisionFacts, ProductGroup, ProviderListing, RankingResult
from app.models.query import ParsedQuery
from app.services import explainer


def _listing(**overrides) -> ProviderListing:
    defaults = dict(
        listing_id="nike-1",
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
        group_id="group-1", canonical_title="Nike Pegasus 41", listings=list(listings), match_confidence=1.0
    )


def test_no_results_explanation() -> None:
    ranking = RankingResult(decision_facts=DecisionFacts(), explanation="")
    text = explainer.generate_explanation([], ranking, ParsedQuery(raw_query="unobtainium sneakers"))
    assert "unobtainium sneakers" in text


def test_cheapest_and_best_deal_are_the_same_listing() -> None:
    listing = _listing()
    groups = [_group(listing)]
    ranking = RankingResult(
        cheapest_listing_id=listing.listing_id,
        best_deal_listing_id=listing.listing_id,
        official_listing_id=listing.listing_id,
        decision_facts=DecisionFacts(
            cheapest_listing_id=listing.listing_id,
            cheapest_total=listing.total_price,
            best_deal_listing_id=listing.listing_id,
            best_deal_total=listing.total_price,
            official_listing_id=listing.listing_id,
            official_total=listing.total_price,
            price_delta_vs_cheapest=0.0,
        ),
        explanation="",
    )
    text = explainer.generate_explanation(groups, ranking, ParsedQuery(raw_query="q"))
    assert "Nike" in text
    assert "$130.00" in text
    assert "best overall deal" in text
    assert "official Nike store" in text


def test_best_deal_differs_from_cheapest_mentions_delta() -> None:
    cheap = _listing(listing_id="ebay-1", provider="ebay", total_price=100.0, price=93.01, shipping=6.99)
    official = _listing(listing_id="nike-1", provider="nike", total_price=101.0, official_store=True, shipping=0.0)
    groups = [_group(cheap, official)]
    ranking = RankingResult(
        cheapest_listing_id=cheap.listing_id,
        best_deal_listing_id=official.listing_id,
        official_listing_id=official.listing_id,
        decision_facts=DecisionFacts(
            cheapest_listing_id=cheap.listing_id,
            cheapest_total=cheap.total_price,
            best_deal_listing_id=official.listing_id,
            best_deal_total=official.total_price,
            best_deal_reason="the official store",
            official_listing_id=official.listing_id,
            official_total=official.total_price,
            price_delta_vs_cheapest=1.0,
        ),
        explanation="",
    )
    text = explainer.generate_explanation(groups, ranking, ParsedQuery(raw_query="q"))
    assert "Ebay" in text or "ebay" in text.lower()
    assert "$1.00 more" in text
    assert "backed by the official store" in text


def test_best_deal_reason_reflects_availability_not_a_hardcoded_guess() -> None:
    """Regression test: the explainer must state the real reason ranking picked a listing
    (e.g. availability), not fall back to a stale 'free shipping' assumption."""
    cheap_but_limited = _listing(listing_id="limited-1", total_price=100.0)
    plentiful = _listing(listing_id="plentiful-1", provider="amazon", total_price=101.5)
    groups = [_group(cheap_but_limited, plentiful)]
    ranking = RankingResult(
        cheapest_listing_id=cheap_but_limited.listing_id,
        best_deal_listing_id=plentiful.listing_id,
        decision_facts=DecisionFacts(
            cheapest_listing_id=cheap_but_limited.listing_id,
            cheapest_total=cheap_but_limited.total_price,
            best_deal_listing_id=plentiful.listing_id,
            best_deal_total=plentiful.total_price,
            best_deal_reason="better stock availability than the cheapest option",
            price_delta_vs_cheapest=1.5,
        ),
        explanation="",
    )
    text = explainer.generate_explanation(groups, ranking, ParsedQuery(raw_query="q"))
    assert "backed by better stock availability" in text
    assert "free shipping" not in text


def test_ai_polish_rejected_when_it_drops_a_price(monkeypatch) -> None:
    monkeypatch.setattr(explainer.config, "azure_openai_configured", lambda: True)

    class _FakeMessage:
        content = "Nike has a great deal for you today!"  # price dropped

    class _FakeChoice:
        message = _FakeMessage()

    class _FakeResponse:
        choices = [_FakeChoice()]

    class _FakeCompletions:
        def create(self, **kwargs):
            return _FakeResponse()

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeClient:
        chat = _FakeChat()

    import openai

    monkeypatch.setattr(openai, "AzureOpenAI", lambda **kwargs: _FakeClient())

    listing = _listing()
    groups = [_group(listing)]
    ranking = RankingResult(
        cheapest_listing_id=listing.listing_id,
        best_deal_listing_id=listing.listing_id,
        decision_facts=DecisionFacts(cheapest_listing_id=listing.listing_id, cheapest_total=listing.total_price),
        explanation="",
    )
    text = explainer.generate_explanation(groups, ranking, ParsedQuery(raw_query="q"))
    assert "$130.00" in text


def test_ai_polish_accepted_when_facts_preserved(monkeypatch) -> None:
    monkeypatch.setattr(explainer.config, "azure_openai_configured", lambda: True)

    class _FakeMessage:
        content = "Great news — Nike has it for $130.00 total, the best price around!"

    class _FakeChoice:
        message = _FakeMessage()

    class _FakeResponse:
        choices = [_FakeChoice()]

    class _FakeCompletions:
        def create(self, **kwargs):
            return _FakeResponse()

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeClient:
        chat = _FakeChat()

    import openai

    monkeypatch.setattr(openai, "AzureOpenAI", lambda **kwargs: _FakeClient())

    listing = _listing()
    groups = [_group(listing)]
    ranking = RankingResult(
        cheapest_listing_id=listing.listing_id,
        best_deal_listing_id=listing.listing_id,
        decision_facts=DecisionFacts(cheapest_listing_id=listing.listing_id, cheapest_total=listing.total_price),
        explanation="",
    )
    text = explainer.generate_explanation(groups, ranking, ParsedQuery(raw_query="q"))
    assert "Great news" in text
