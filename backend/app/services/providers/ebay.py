from app.models.product import ProviderListing
from app.models.query import ParsedQuery
from app.services.providers.base import Provider, search_provider_inventory


class EbayProvider(Provider):
    """eBay marketplace — third-party sellers; listings never carry a manufacturer SKU."""

    name = "ebay"

    def search(self, parsed_query: ParsedQuery) -> list[ProviderListing]:
        return search_provider_inventory(self.name, parsed_query)
