"""A tiny orders module: line-item totals, paid status, and discounts."""


def total_for(order):
    """Sum the line items on an order."""
    return sum(li.qty * li.price for li in order.lines)


def is_paid(order):
    return order.amount_paid >= total_for(order)


def apply_discount(order, pct):
    """Return the order total after a percentage discount."""
    return total_for(order) * (1 - pct / 100)
