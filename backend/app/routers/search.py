import asyncio
import logging

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, field_validator

from app.models.product import ProviderListing, SearchResponse
from app.models.query import ParsedQuery
from app.services.explainer import generate_explanation
from app.services.matcher import match_listings
from app.services.parser import parse_query
from app.services.provider_selector import get_provider_selector
from app.services.providers.base import Provider
from app.services.providers.registry import get_providers
from app.services.ranking import rank_products

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)

    @field_validator("query")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must not be blank")
        return value


async def _search_provider_safely(provider: Provider, parsed_query: ParsedQuery) -> list[ProviderListing]:
    """Isolate one provider's failure so it can't take down the whole search."""
    try:
        return await run_in_threadpool(provider.search, parsed_query)
    except Exception:
        logger.exception("Provider %r failed to search; continuing without its results.", provider.name)
        return []


@router.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    try:
        parsed_query = parse_query(request.query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to parse the search query.") from exc

    try:
        providers_by_name = {provider.name: provider for provider in get_providers()}
        selections = get_provider_selector().select(parsed_query, list(providers_by_name.keys()))

        # Step 4: query the selected providers concurrently rather than one at a time.
        results = await asyncio.gather(
            *(_search_provider_safely(providers_by_name[selection.provider], parsed_query) for selection in selections)
        )
        all_listings = [listing for provider_listings in results for listing in provider_listings]

        groups = match_listings(all_listings)
        ranking = rank_products(groups, parsed_query)
        ranking.explanation = generate_explanation(groups, ranking, parsed_query)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to process the search request.") from exc

    return SearchResponse(
        parsed_query=parsed_query,
        provider_selection=selections,
        providers_searched=[selection.provider for selection in selections],
        groups=groups,
        ranking=ranking,
    )


@router.get("/api/providers")
def list_providers() -> list[dict[str, str]]:
    return [{"name": provider.name} for provider in get_providers()]
