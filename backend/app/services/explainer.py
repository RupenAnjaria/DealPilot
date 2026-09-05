import logging
from typing import Optional

from app.models.product import DecisionFacts, ProductGroup, ProviderListing, RankingResult
from app.models.query import ParsedQuery
from app.services.ai.client import get_ai_client

logger = logging.getLogger(__name__)

# Sanity bound on AI-polished explanation length; a factual 2-3 sentence summary should
# never legitimately be this long, so anything longer signals a malformed response.
_MAX_POLISHED_LENGTH = 1000


def _find_listing(groups: list[ProductGroup], listing_id: Optional[str]) -> Optional[ProviderListing]:
    if not listing_id:
        return None
    for group in groups:
        for listing in group.listings:
            if listing.listing_id == listing_id:
                return listing
    return None


def _money(value: float) -> str:
    return f"${value:.2f}"


def _template_explanation(groups: list[ProductGroup], ranking: RankingResult, parsed_query: ParsedQuery) -> str:
    facts = ranking.decision_facts
    cheapest = _find_listing(groups, ranking.cheapest_listing_id)
    if cheapest is None:
        return f'No matching products were found for "{parsed_query.raw_query}". Try adjusting size, color, or price.'

    best_deal = _find_listing(groups, ranking.best_deal_listing_id)
    official = _find_listing(groups, ranking.official_listing_id)

    sentences = [
        f"{cheapest.provider.title()} has the cheapest option at {_money(cheapest.total_price)} total "
        f"({_money(cheapest.price)} + {_money(cheapest.shipping)} shipping)."
    ]

    if best_deal is not None and best_deal.listing_id != cheapest.listing_id:
        delta = facts.price_delta_vs_cheapest or 0.0
        reason = facts.best_deal_reason or "a stronger overall deal"
        sentences.append(
            f"{best_deal.provider.title()} is the best overall deal at {_money(best_deal.total_price)} total — "
            f"only {_money(delta)} more than the cheapest option, backed by {reason}."
        )
    elif best_deal is not None:
        sentences.append("That's also the best overall deal.")

    if official is not None and official.listing_id not in {cheapest.listing_id, getattr(best_deal, "listing_id", None)}:
        sentences.append(
            f"Buying directly from {official.brand}'s official store costs {_money(official.total_price)} total."
        )
    elif official is not None and official.listing_id == cheapest.listing_id:
        sentences.append(f"It's also the official {official.brand} store.")

    return " ".join(sentences)


_AI_SYSTEM_PROMPT = (
    "Rephrase the following factual product-deal explanation to sound natural and friendly. "
    "Do not change, add, or remove any prices, numbers, or facts — only improve the wording. "
    "Keep it to 2-3 short sentences."
)


def _ai_polish(template: str, facts: DecisionFacts) -> Optional[str]:
    """Rephrase the deterministic template. May only change wording, never the facts.

    Uses whatever AI client is configured (Azure OpenAI or an OpenAI-compatible endpoint)
    via get_ai_client(); returns None immediately in DEMO MODE, and returns None on any
    failure or validation problem so generate_explanation() falls back to the template.
    """
    client = get_ai_client()
    if client is None:
        return None
    try:
        polished = client.complete_text(_AI_SYSTEM_PROMPT, template)
    except Exception:
        logger.warning("AI explanation polish raised unexpectedly; using the template instead.", exc_info=True)
        return None
    if not polished:
        return None
    if len(polished) > _MAX_POLISHED_LENGTH:
        logger.warning("AI explanation polish returned unexpectedly long text (%d chars); discarding.", len(polished))
        return None
    # Guard against the model silently altering the numbers it was told not to touch.
    for total in (facts.cheapest_total, facts.best_deal_total, facts.official_total):
        if total is not None and _money(total) not in polished:
            return None
    return polished.strip()


def generate_explanation(groups: list[ProductGroup], ranking: RankingResult, parsed_query: ParsedQuery) -> str:
    """Natural-language summary of the ranking. AI (if configured) may only rephrase, never recompute."""
    template = _template_explanation(groups, ranking, parsed_query)
    polished = _ai_polish(template, ranking.decision_facts)
    return polished or template
