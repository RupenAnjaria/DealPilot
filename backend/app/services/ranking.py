from app.models.product import DecisionFacts, ProductGroup, ProviderListing, RankingResult
from app.models.query import ParsedQuery

# Small, deterministic tie-break adjustments used only to pick the "best overall deal"
# by total delivered price (item price + shipping). Tune freely — ranking always stays a
# numeric formula; no AI is involved in computing any of these numbers.
OFFICIAL_STORE_BONUS = 3.0  # $ credit for buying from the brand's own official store
LIMITED_AVAILABILITY_PENALTY = 2.0  # $ penalty for "limited" stock vs. fully "in_stock"
LOW_CONFIDENCE_PENALTY_WEIGHT = 5.0  # $ penalty per unit of (1 - product match confidence)

_MATCHABLE_ATTRIBUTES = ["brand", "model", "category", "gender", "size", "color", "sku"]


def _matched_attributes(parsed_query: ParsedQuery) -> list[str]:
    """Which requested attributes were specific enough to constrain the search."""
    return [attr for attr in _MATCHABLE_ATTRIBUTES if getattr(parsed_query, attr) is not None]


def _best_deal_score(listing: ProviderListing, match_confidence: float) -> float:
    """Lower is better. Starts from total delivered price, then applies small adjustments."""
    score = listing.total_price
    if listing.official_store:
        score -= OFFICIAL_STORE_BONUS
    if listing.availability == "limited":
        score += LIMITED_AVAILABILITY_PENALTY
    score += (1 - match_confidence) * LOW_CONFIDENCE_PENALTY_WEIGHT
    return score


def _best_deal_reason(
    best_deal: ProviderListing,
    best_deal_confidence: float,
    cheapest: ProviderListing,
    cheapest_confidence: float,
) -> str:
    """Which adjustment (mirrors _best_deal_score) tipped the pick away from the cheapest
    delivered price. Computed once here so the explainer never has to guess or duplicate
    this logic — it only ever restates a fact ranking already decided.
    """
    if best_deal.official_store and not cheapest.official_store:
        return "the official store"
    if cheapest.availability == "limited" and best_deal.availability != "limited":
        return "better stock availability than the cheapest option"
    if best_deal_confidence > cheapest_confidence:
        return "a more confidently matched listing"
    return "a stronger overall deal"


def rank_products(groups: list[ProductGroup], parsed_query: ParsedQuery) -> RankingResult:
    """Rank normalized listings by total delivered price (item price + shipping). No AI here."""
    attributes_matched = _matched_attributes(parsed_query)

    # Pair each purchasable listing with its group's match confidence (how sure we are
    # that grouping listings from different retailers as "the same product" was correct).
    available = [
        (listing, group.match_confidence)
        for group in groups
        for listing in group.listings
        if listing.availability != "out_of_stock"
    ]

    if not available:
        return RankingResult(
            decision_facts=DecisionFacts(attributes_matched=attributes_matched),
            # Filled in by the explainer once results (or lack thereof) are known.
            explanation="",
        )

    all_listings = [listing for listing, _confidence in available]

    cheapest_item = min(all_listings, key=lambda listing: listing.price)
    cheapest_delivered = min(all_listings, key=lambda listing: listing.total_price)
    official_listings = [listing for listing in all_listings if listing.official_store]
    official = min(official_listings, key=lambda listing: listing.total_price) if official_listings else None
    best_deal, best_deal_confidence = min(available, key=lambda pair: _best_deal_score(*pair))

    best_deal_reason = None
    if best_deal.listing_id != cheapest_delivered.listing_id:
        cheapest_confidence = next(
            confidence for listing, confidence in available if listing.listing_id == cheapest_delivered.listing_id
        )
        best_deal_reason = _best_deal_reason(best_deal, best_deal_confidence, cheapest_delivered, cheapest_confidence)

    facts = DecisionFacts(
        cheapest_item_listing_id=cheapest_item.listing_id,
        cheapest_item_price=cheapest_item.price,
        cheapest_listing_id=cheapest_delivered.listing_id,
        cheapest_total=cheapest_delivered.total_price,
        best_deal_listing_id=best_deal.listing_id,
        best_deal_total=best_deal.total_price,
        best_deal_reason=best_deal_reason,
        official_listing_id=official.listing_id if official else None,
        official_total=official.total_price if official else None,
        price_delta_vs_cheapest=round(best_deal.total_price - cheapest_delivered.total_price, 2),
        attributes_matched=attributes_matched,
    )
    return RankingResult(
        cheapest_listing_id=cheapest_delivered.listing_id,
        best_deal_listing_id=best_deal.listing_id,
        official_listing_id=official.listing_id if official else None,
        decision_facts=facts,
        explanation="",
    )

