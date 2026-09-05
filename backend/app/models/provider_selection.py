from pydantic import BaseModel


class ProviderSelection(BaseModel):
    """One retailer chosen to be searched for a given request, and why."""

    provider: str
    # 1 = searched first/most important; ties are broken by list order.
    priority: int
    reason: str
