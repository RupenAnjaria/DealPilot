import pytest

from app.services import parser


def test_full_query_extracts_all_attributes() -> None:
    parsed = parser.rule_based_parse("Find Nike Pegasus 41 men's size 10 black under $120")
    assert parsed.brand == "Nike"
    assert parsed.model == "Pegasus 41"
    assert parsed.gender == "men"
    assert parsed.size == "10"
    assert parsed.color == "black"
    assert parsed.max_price == 120.0
    assert parsed.parse_method == "rule_based"


def test_women_gender_not_confused_with_men() -> None:
    parsed = parser.rule_based_parse("Nike Pegasus 41 women's size 8 pink")
    assert parsed.gender == "women"


def test_sku_extraction() -> None:
    parsed = parser.rule_based_parse("Nike DV3853-001 size 10")
    assert parsed.sku == "DV3853-001"


def test_ambiguous_query_without_brand_or_model() -> None:
    parsed = parser.rule_based_parse("running shoes under $150")
    assert parsed.brand is None
    assert parsed.model is None
    assert parsed.category == "running shoes"
    assert parsed.max_price == 150.0


@pytest.mark.parametrize(
    "query, expected",
    [
        (
            "Find Nike Pegasus 41 men's size 10 black under $120",
            {"brand": "Nike", "model": "Pegasus 41", "gender": "men", "size": "10", "color": "black", "max_price": 120.0},
        ),
        (
            "Nike Pegasus 41 women's size 8 pink",
            {"brand": "Nike", "model": "Pegasus 41", "gender": "women", "size": "8", "color": "pink"},
        ),
        (
            "Nike Air Max 270 size 9 white under $160",
            {"brand": "Nike", "model": "Air Max 270", "size": "9", "color": "white", "max_price": 160.0},
        ),
        (
            "Nike Air Force 1 '07 black size 11",
            {"brand": "Nike", "model": "Air Force 1 '07", "color": "black", "size": "11"},
        ),
        (
            "Looking for Nike Vomero 17 size 10 black max $150",
            {"brand": "Nike", "model": "Vomero 17", "size": "10", "color": "black", "max_price": 150.0},
        ),
        (
            "Nike Pegasus 40 blue size 9 below $100",
            {"brand": "Nike", "model": "Pegasus 40", "color": "blue", "size": "9", "max_price": 100.0},
        ),
        (
            "Nike Air Max 270 React grey size 10",
            {"brand": "Nike", "model": "Air Max 270 React", "color": "grey", "size": "10"},
        ),
        (
            "Nike Air Force 1 Shadow women's pink size 8",
            {"brand": "Nike", "model": "Air Force 1 Shadow", "gender": "women", "color": "pink", "size": "8"},
        ),
        (
            "Nike Vomero 18 white size 11 less than $170",
            {"brand": "Nike", "model": "Vomero 18", "color": "white", "size": "11", "max_price": 170.0},
        ),
        (
            "Nike Pegasus 41 men's size 10.5 black",
            {"brand": "Nike", "model": "Pegasus 41", "gender": "men", "size": "10.5", "color": "black"},
        ),
        (
            "Nike DV3853-001 size 10",
            {"brand": "Nike", "sku": "DV3853-001", "size": "10"},
        ),
        (
            "adidas Ultraboost 22 size 10 black under $200",
            {"brand": "Adidas", "model": "Ultraboost 22", "size": "10", "color": "black", "max_price": 200.0},
        ),
        (
            "Nike Pegasus 41 $100 or less",
            {"brand": "Nike", "model": "Pegasus 41", "max_price": 100.0},
        ),
        (
            "Nike running shoes size 10 under $150",
            {"brand": "Nike", "category": "running shoes", "size": "10", "max_price": 150.0},
        ),
        (
            "Levi's 501 Original size 34 blue",
            {"brand": "Levi's", "model": "501 Original", "size": "34", "color": "blue"},
        ),
        (
            "Nike Air Force 1 '07 white size 9 maximum 130",
            {"brand": "Nike", "model": "Air Force 1 '07", "color": "white", "size": "9", "max_price": 130.0},
        ),
        (
            "running shoes under $150",
            {"brand": None, "model": None, "category": "running shoes", "max_price": 150.0},
        ),
        (
            "comfortable jogging shoes for my dad",
            {"brand": None, "model": None},
        ),
    ],
)
def test_rule_based_parse_common_patterns(query: str, expected: dict) -> None:
    parsed = parser.rule_based_parse(query)
    for field, value in expected.items():
        assert getattr(parsed, field) == value, f"{field} mismatch for query: {query!r}"


def test_parse_query_stays_rule_based_when_azure_not_configured(monkeypatch) -> None:
    monkeypatch.setattr("app.config.azure_openai_configured", lambda: False)
    parsed = parser.parse_query("running shoes under $150")
    assert parsed.parse_method == "rule_based"


def test_parse_query_uses_ai_only_when_ambiguous(monkeypatch) -> None:
    calls = []

    def fake_parse(self, raw_query: str):
        calls.append(raw_query)
        return parser.ParsedQuery(raw_query=raw_query, brand="Nike", parse_method="ai")

    monkeypatch.setattr(parser.AIQueryParser, "parse", fake_parse)

    # Clear query: AI must not be called.
    parser.parse_query("Nike Pegasus 41 men's size 10 black under $120")
    assert calls == []

    # Ambiguous query: AI fallback should be invoked.
    result = parser.parse_query("comfortable jogging shoes for my dad")
    assert calls == ["comfortable jogging shoes for my dad"]
    assert result.parse_method == "ai"
    assert result.brand == "Nike"


def test_ai_parse_failure_falls_back_silently(monkeypatch) -> None:
    # Configured but with no real endpoint/key -> the Azure client call inside
    # AIQueryParser.parse must fail and be caught, falling back to the rule-based result.
    monkeypatch.setattr("app.config.azure_openai_configured", lambda: True)
    result = parser.parse_query("comfortable jogging shoes for my dad")
    assert result.parse_method == "rule_based"


def test_get_query_parser_returns_fallback_composition() -> None:
    query_parser = parser.get_query_parser()
    assert isinstance(query_parser, parser.FallbackQueryParser)
    assert isinstance(query_parser._primary, parser.RuleBasedParser)
    assert isinstance(query_parser._fallback, parser.AIQueryParser)
