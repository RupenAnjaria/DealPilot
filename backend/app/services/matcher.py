import logging
import re
from dataclasses import dataclass, field
from typing import Literal, Optional

from pydantic import BaseModel, ValidationError
from rapidfuzz import fuzz

from app.models.product import ProductGroup, ProviderListing
from app.services.ai.client import get_ai_client

logger = logging.getLogger(__name__)

# Weights reflect the requested priority order (SKU is handled separately, below, as an
# absolute override rather than a weighted signal). They must sum to 1.0.
FIELD_WEIGHTS = {
    "brand": 0.28,
    "model": 0.24,
    "gender": 0.15,
    "size": 0.13,
    "color": 0.11,
    "title": 0.09,
}

# brand/model/gender are treated as critical identifiers: if both listings report a value
# and it differs, they cannot be the same product, no matter how similar anything else is.
# Size/color/title are supporting signals only, so they never veto a match, only nudge the
# score: query-time filtering already guarantees every returned listing matches the size the
# user asked for (when they asked for one), so a differing *default* size across retailers
# (when the user didn't ask for one) must not fragment otherwise-identical products.
_CRITICAL_FIELDS = ("brand", "model", "gender")

# Minimum confidence to treat two listings as the same underlying product.
MATCH_THRESHOLD = 0.75

# Deterministic scores in this band are genuinely ambiguous: not confidently a match, but
# not confidently a conflict either. Only in this narrow range do we consult AI (if
# configured) to break the tie — it can only flip is_match, never the score itself.
_AI_TIEBREAK_LOW = 0.55

_AI_MATCH_SYSTEM_PROMPT = (
    "Decide whether two retail product listings describe the exact same underlying product "
    "(same brand, model, size, and color), just worded differently by different sellers. "
    'Respond with a JSON object: {"same_product": true or false}.'
)


class _AIMatchVerdict(BaseModel):
    """Type-checked shape for the AI's tie-break response — never trust the raw JSON."""

    same_product: bool


def _ask_ai_same_product(listing_a: ProviderListing, listing_b: ProviderListing) -> Optional[bool]:
    """Consult AI only for a genuinely ambiguous pair. Returns None (defer to the
    deterministic threshold) in DEMO MODE or on any failure/invalid response."""
    client = get_ai_client()
    if client is None:
        return None
    user_prompt = (
        f"Listing A: brand={listing_a.brand}, model={listing_a.model}, gender={listing_a.gender}, "
        f"size={listing_a.size}, color={listing_a.color}, title={listing_a.title!r}\n"
        f"Listing B: brand={listing_b.brand}, model={listing_b.model}, gender={listing_b.gender}, "
        f"size={listing_b.size}, color={listing_b.color}, title={listing_b.title!r}"
    )
    try:
        data = client.complete_json(_AI_MATCH_SYSTEM_PROMPT, user_prompt)
        if data is None:
            return None
        return _AIMatchVerdict.model_validate(data).same_product
    except ValidationError:
        logger.warning("AI match verdict failed validation; deferring to the deterministic score.")
        return None
    except Exception:
        logger.warning("AI match tie-break raised unexpectedly; deferring to the deterministic score.", exc_info=True)
        return None


@dataclass
class MatchResult:
    """Pairwise match confidence (0-1) between two listings, with a field-by-field explanation."""

    score: float
    is_match: bool
    method: Literal["deterministic", "ai"] = "deterministic"
    explanation: list[str] = field(default_factory=list)


def _normalize(value: Optional[str]) -> Optional[str]:
    return value.strip().lower() if value else None


def _normalize_sku(value: Optional[str]) -> Optional[str]:
    """Strip punctuation/whitespace so 'DV3853-001' and 'DV3853001' compare equal."""
    if not value:
        return None
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _field_signal(value_a: Optional[str], value_b: Optional[str]) -> str:
    """'match' | 'conflict' | 'unknown' for a normalized exact-value comparison."""
    normalized_a, normalized_b = _normalize(value_a), _normalize(value_b)
    if normalized_a is None or normalized_b is None:
        return "unknown"
    return "match" if normalized_a == normalized_b else "conflict"


def compare_listings(listing_a: ProviderListing, listing_b: ProviderListing) -> MatchResult:
    """Deterministic pairwise match confidence, weighted SKU > brand > model > gender >
    size > color > title similarity (roughly, per FIELD_WEIGHTS). No LLM involved.
    """
    sku_a, sku_b = _normalize_sku(listing_a.sku), _normalize_sku(listing_b.sku)
    if sku_a is not None and sku_b is not None:
        if sku_a == sku_b:
            return MatchResult(
                score=1.0,
                is_match=True,
                explanation=[f"Exact SKU match ('{listing_a.sku}' \u2248 '{listing_b.sku}') \u2014 conclusive."],
            )
        return MatchResult(
            score=0.0,
            is_match=False,
            explanation=[f"Different SKUs ('{listing_a.sku}' vs '{listing_b.sku}') \u2014 different products."],
        )

    explanation: list[str] = []
    weighted_sum = 0.0
    total_weight = 0.0

    for field_name in _CRITICAL_FIELDS:
        weight = FIELD_WEIGHTS[field_name]
        value_a, value_b = getattr(listing_a, field_name), getattr(listing_b, field_name)
        signal = _field_signal(value_a, value_b)
        if signal == "unknown":
            explanation.append(f"{field_name.title()} unknown on at least one side \u2014 not counted.")
            continue
        if signal == "conflict":
            explanation.append(
                f"{field_name.title()} differs ('{value_a}' vs '{value_b}') \u2014 "
                "critical identifier conflict, cannot be the same product."
            )
            return MatchResult(score=0.0, is_match=False, explanation=explanation)
        total_weight += weight
        weighted_sum += weight
        explanation.append(f"{field_name.title()} matches ('{value_a}').")

    color_ratio = fuzz.partial_ratio(_normalize(listing_a.color) or "", _normalize(listing_b.color) or "") / 100
    weighted_sum += FIELD_WEIGHTS["color"] * color_ratio
    total_weight += FIELD_WEIGHTS["color"]
    explanation.append(f"Color similarity {color_ratio:.0%} ('{listing_a.color}' vs '{listing_b.color}').")

    size_signal = _field_signal(listing_a.size, listing_b.size)
    if size_signal == "unknown":
        explanation.append("Size unknown on at least one side \u2014 not counted.")
    else:
        total_weight += FIELD_WEIGHTS["size"]
        if size_signal == "match":
            weighted_sum += FIELD_WEIGHTS["size"]
            explanation.append(f"Size matches ('{listing_a.size}').")
        else:
            explanation.append(
                f"Size differs ('{listing_a.size}' vs '{listing_b.size}') \u2014 "
                "noted, but not disqualifying since it may just be each retailer's default."
            )

    title_ratio = fuzz.token_sort_ratio(listing_a.title, listing_b.title) / 100
    weighted_sum += FIELD_WEIGHTS["title"] * title_ratio
    total_weight += FIELD_WEIGHTS["title"]
    explanation.append(f"Title similarity {title_ratio:.0%} ('{listing_a.title}' vs '{listing_b.title}').")

    score = round(weighted_sum / total_weight, 4) if total_weight else 0.0

    if _AI_TIEBREAK_LOW <= score < MATCH_THRESHOLD:
        ai_verdict = _ask_ai_same_product(listing_a, listing_b)
        if ai_verdict is not None:
            explanation.append(
                f"Score was ambiguous ({score:.0%}); AI judged same_product={ai_verdict}."
            )
            return MatchResult(score=score, is_match=ai_verdict, method="ai", explanation=explanation)

    return MatchResult(score=score, is_match=score >= MATCH_THRESHOLD, explanation=explanation)


def _canonical_title(listing: ProviderListing) -> str:
    return f"{listing.brand or ''} {listing.model or ''}".strip() or listing.title


@dataclass
class _WorkingGroup:
    listings: list[ProviderListing] = field(default_factory=list)
    match_confidence: float = 1.0
    match_method: Literal["deterministic", "ai"] = "deterministic"


def match_listings(listings: list[ProviderListing]) -> list[ProductGroup]:
    """Group listings from different providers that represent the same underlying product,
    using compare_listings() against each group's first (representative) listing.
    """
    groups: list[_WorkingGroup] = []

    for listing in listings:
        best_group, best_score, best_method = None, 0.0, "deterministic"
        for group in groups:
            result = compare_listings(listing, group.listings[0])
            if result.is_match and result.score > best_score:
                best_group, best_score, best_method = group, result.score, result.method

        if best_group is not None:
            best_group.listings.append(listing)
            best_group.match_confidence = min(best_group.match_confidence, best_score)
            if best_method == "ai":
                best_group.match_method = "ai"
        else:
            groups.append(_WorkingGroup(listings=[listing]))

    return [
        ProductGroup(
            group_id=f"group-{i + 1}",
            canonical_title=_canonical_title(group.listings[0]),
            listings=group.listings,
            match_confidence=round(group.match_confidence, 4),
            match_method=group.match_method,
        )
        for i, group in enumerate(groups)
    ]

