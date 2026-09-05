from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_providers_endpoint_lists_all_four() -> None:
    response = client.get("/api/providers")
    assert response.status_code == 200
    names = {p["name"] for p in response.json()}
    assert names == {"nike", "amazon", "walmart", "ebay"}


def test_search_full_query_returns_ranked_groups() -> None:
    response = client.post(
        "/api/search", json={"query": "Find Nike Pegasus 41 men's size 10 black under $200"}
    )
    assert response.status_code == 200
    body = response.json()

    assert body["parsed_query"]["brand"] == "Nike"
    assert body["parsed_query"]["max_price"] == 200.0

    assert len(body["groups"]) >= 1
    all_listing_ids = {listing["listing_id"] for group in body["groups"] for listing in group["listings"]}

    ranking = body["ranking"]
    assert ranking["cheapest_listing_id"] in all_listing_ids
    assert ranking["best_deal_listing_id"] in all_listing_ids
    assert ranking["official_listing_id"] in all_listing_ids
    assert ranking["decision_facts"]["cheapest_total"] is not None
    assert ranking["explanation"] != ""


def test_search_with_no_matches_returns_empty_groups() -> None:
    response = client.post("/api/search", json={"query": "Nike Pegasus 41 size 999 under $1"})
    assert response.status_code == 200
    body = response.json()
    assert body["groups"] == []
    assert body["ranking"]["cheapest_listing_id"] is None
    assert "No matching products" in body["ranking"]["explanation"]


def test_search_response_includes_provider_selection_and_providers_searched() -> None:
    response = client.post("/api/search", json={"query": "Nike Pegasus 41 size 10 black"})
    assert response.status_code == 200
    body = response.json()

    assert body["providers_searched"] == ["nike", "amazon", "walmart", "ebay"]
    assert {selection["provider"] for selection in body["provider_selection"]} == {
        "nike", "amazon", "walmart", "ebay",
    }
    nike_selection = next(s for s in body["provider_selection"] if s["provider"] == "nike")
    assert nike_selection["priority"] == 1
    assert "Nike" in nike_selection["reason"]
    assert all("reason" in s and s["reason"] for s in body["provider_selection"])


def test_search_response_excludes_official_store_for_a_different_brand() -> None:
    response = client.post("/api/search", json={"query": "Adidas Ultraboost 22 size 10 black"})
    assert response.status_code == 200
    body = response.json()
    assert "nike" not in body["providers_searched"]


def test_search_rejects_blank_query() -> None:
    response = client.post("/api/search", json={"query": "   "})
    assert response.status_code == 422


def test_search_for_unrecognized_product_returns_no_groups() -> None:
    # Regression test: a product the parser can't recognize at all (no brand/model/sku/
    # category) must not fall back to returning every unrelated catalog item.
    response = client.post("/api/search", json={"query": "cannon camera sku 334455"})
    assert response.status_code == 200
    body = response.json()
    assert body["groups"] == []
    assert body["ranking"]["cheapest_listing_id"] is None


def test_search_rejects_missing_query_field() -> None:
    response = client.post("/api/search", json={})
    assert response.status_code == 422


def test_search_survives_a_single_provider_failure(monkeypatch) -> None:
    from app.services.providers.ebay import EbayProvider

    def _boom(self, parsed_query):
        raise RuntimeError("simulated eBay outage")

    monkeypatch.setattr(EbayProvider, "search", _boom)

    response = client.post(
        "/api/search", json={"query": "Find Nike Pegasus 41 men's size 10 black under $200"}
    )
    assert response.status_code == 200
    body = response.json()
    all_providers = {listing["provider"] for group in body["groups"] for listing in group["listings"]}
    assert "ebay" not in all_providers
    assert len(body["groups"]) >= 1
