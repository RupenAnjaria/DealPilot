from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ParsedQuery(BaseModel):
    """Normalized product search request extracted from a natural-language search."""

    raw_query: str
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    gender: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    sku: Optional[str] = None
    max_price: Optional[float] = None
    # Leftover free-text terms not captured by a structured field above.
    keywords: List[str] = Field(default_factory=list)
    # Which parser produced this result; surfaced so the UI/tests can show provenance.
    parse_method: Literal["rule_based", "ai"] = "rule_based"

    @field_validator("max_price")
    @classmethod
    def _max_price_positive(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value <= 0:
            raise ValueError("max_price must be > 0")
        return value
