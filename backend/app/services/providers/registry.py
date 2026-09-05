from app.services.providers.amazon import AmazonProvider
from app.services.providers.base import Provider
from app.services.providers.ebay import EbayProvider
from app.services.providers.nike import NikeProvider
from app.services.providers.walmart import WalmartProvider


def get_providers() -> list[Provider]:
    """All mock providers; app/services/provider_selector.py decides which of these to search."""
    return [NikeProvider(), AmazonProvider(), WalmartProvider(), EbayProvider()]
