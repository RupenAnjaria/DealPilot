def calculate_total_price(price: float, shipping_cost: float) -> float:
    """Total delivered price for a listing. The only place item + shipping math happens."""
    return round(price + shipping_cost, 2)
