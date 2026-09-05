import re
from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel, ValidationError

from app.models.query import ParsedQuery
from app.services.ai.client import get_ai_client
from app.services.providers.base import load_catalog

COLOR_WORDS = [
    "black", "white", "grey", "gray", "red", "blue", "pink", "green", "navy", "brown", "tan",
]
# Longest/plural phrases first so "running shoes" wins over "running shoe" wins over "shoes".
CATEGORY_WORDS = [
    "running shoes", "running shoe", "sneakers", "shoes", "shoe", "jeans", "pants", "jacket", "shirt", "boots",
]

_MAX_PRICE_PATTERNS = [
    re.compile(r"(?:under|below|less than|maximum)\s*\$?\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"\$\s*(\d+(?:\.\d+)?)\s*or less", re.IGNORECASE),
    # Bare "max" requires an explicit "$" so it doesn't collide with product names like "Air Max".
    re.compile(r"\bmax\s*\$\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
]
_SKU_PATTERN = re.compile(r"\b([A-Za-z]{1,4}\d{3,6}-\d{2,4}|[A-Za-z]{2,4}\d{4,8})\b")
_SIZE_PATTERN = re.compile(r"size\s+(\d+(?:\.\d+)?)", re.IGNORECASE)


def _extract_max_price(text: str) -> Optional[float]:
    for pattern in _MAX_PRICE_PATTERNS:
        match = pattern.search(text)
        if match:
            return float(match.group(1))
    return None


def _extract_sku(raw_query: str) -> Optional[str]:
    match = _SKU_PATTERN.search(raw_query)
    return match.group(1).upper() if match else None


def _extract_size(text: str) -> Optional[str]:
    match = _SIZE_PATTERN.search(text)
    return match.group(1) if match else None


def _extract_gender(text: str) -> Optional[str]:
    # Check women/female first since "women's" contains "men's" as a substring.
    if re.search(r"\bwomen'?s\b|\bwomens\b|\bfemale\b", text):
        return "women"
    if re.search(r"\bmen'?s\b|\bmens\b|\bmale\b", text):
        return "men"
    if "unisex" in text:
        return "unisex"
    return None


def _extract_color(text: str) -> Optional[str]:
    for color in sorted(COLOR_WORDS, key=len, reverse=True):
        if re.search(rf"\b{color}\b", text):
            return color
    return None


def _extract_category(text: str) -> Optional[str]:
    for category in CATEGORY_WORDS:
        if category in text:
            return category
    return None


def _extract_brand_and_model(text: str) -> tuple[Optional[str], Optional[str]]:
    """Match brand/model against the provider catalog so the parser stays in sync with it."""
    best_brand, best_model, best_model_len = None, None, -1
    for entry in load_catalog():
        brand, model = entry["brand"], entry["model"]
        if brand.lower() not in text:
            continue
        if best_brand is None:
            best_brand = brand
        if model.lower() in text and len(model) > best_model_len:
            best_model, best_model_len = model, len(model)
    return best_brand, best_model


def _is_ambiguous(parsed: ParsedQuery) -> bool:
    """Neither a brand nor a model was found — a case worth an AI assist."""
    return parsed.brand is None and parsed.model is None


class QueryParser(ABC):
    """Interface for turning a natural-language search into a normalized ParsedQuery.

    Kept abstract so an AI-backed implementation can be added or swapped in later
    (see AIQueryParser) without changing anything that calls parse_query().
    """

    @abstractmethod
    def parse(self, raw_query: str) -> Optional[ParsedQuery]:
        """Return a ParsedQuery, or None if this parser can't/won't handle the query."""
        raise NotImplementedError


class RuleBasedParser(QueryParser):
    """Deterministic regex/keyword parsing against the known product catalog. No AI required."""

    def parse(self, raw_query: str) -> ParsedQuery:
        text = raw_query.lower()
        brand, model = _extract_brand_and_model(text)
        return ParsedQuery(
            raw_query=raw_query,
            brand=brand,
            model=model,
            category=_extract_category(text),
            gender=_extract_gender(text),
            size=_extract_size(text),
            color=_extract_color(text),
            sku=_extract_sku(raw_query),
            max_price=_extract_max_price(text),
            parse_method="rule_based",
        )


_AI_SYSTEM_PROMPT = (
    "Extract structured shopping attributes from a natural-language product search. "
    "Respond with a JSON object with these keys (use null when not present in the query): "
    "brand, model, category, gender (men/women/unisex), size, color, sku, max_price (number)."
)


class _AIParsedFields(BaseModel):
    """Allow-listed, type-checked shape for the AI's raw JSON response.

    Validating against this (rather than trusting the JSON directly) means an AI response
    with the wrong types, unexpected keys, or garbage values can never reach ParsedQuery.
    """

    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    gender: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    sku: Optional[str] = None
    max_price: Optional[float] = None


class AIQueryParser(QueryParser):
    """AI-backed parser, used as a fallback when rule-based parsing is ambiguous.

    Works with whatever AI client is configured (Azure OpenAI or an OpenAI-compatible
    endpoint) via get_ai_client(); returns None immediately in DEMO MODE (no client
    configured), and returns None on any failure so parse_query() falls back silently.
    """

    def parse(self, raw_query: str) -> Optional[ParsedQuery]:
        client = get_ai_client()
        if client is None:
            return None
        try:
            data = client.complete_json(_AI_SYSTEM_PROMPT, raw_query)
            if data is None:
                return None
            fields = _AIParsedFields.model_validate(data)
            return ParsedQuery(raw_query=raw_query, parse_method="ai", **fields.model_dump())
        except ValidationError:
            # AI returned a shape/type we don't trust — fall back rather than guess.
            return None
        except Exception:
            # Any other AI failure (network, auth, bad response) must fall back silently.
            return None


class FallbackQueryParser(QueryParser):
    """Tries a primary parser first; only consults the fallback when the result is ambiguous."""

    def __init__(self, primary: QueryParser, fallback: QueryParser):
        self._primary = primary
        self._fallback = fallback

    def parse(self, raw_query: str) -> ParsedQuery:
        primary_result = self._primary.parse(raw_query)
        if primary_result is not None and not _is_ambiguous(primary_result):
            return primary_result
        fallback_result = self._fallback.parse(raw_query)
        return fallback_result if fallback_result is not None else primary_result


def get_query_parser() -> QueryParser:
    """Swap point: change this composition to add/replace/reorder parsing strategies."""
    return FallbackQueryParser(primary=RuleBasedParser(), fallback=AIQueryParser())


def rule_based_parse(raw_query: str) -> ParsedQuery:
    return RuleBasedParser().parse(raw_query)


def parse_query(raw_query: str) -> ParsedQuery:
    """Rule-based parsing first; AI is only consulted when it can't find a brand/model."""
    return get_query_parser().parse(raw_query)

