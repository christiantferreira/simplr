"""
Decimal utilities for Simplr.
All monetary calculations use Python Decimal with Banker's rounding.
"""

from decimal import Decimal, ROUND_HALF_EVEN, getcontext

# Set high precision for intermediate calculations
getcontext().prec = 28

ZERO = Decimal("0")
ONE = Decimal("1")
TWO = Decimal("2")
TWELVE = Decimal("12")
HUNDRED = Decimal("100")
PENNY = Decimal("0.01")


def to_decimal(value) -> Decimal:
    """Convert any numeric value to Decimal. Raises ValueError if not convertible."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        # Convert float via string to avoid floating-point artifacts
        return Decimal(str(value))
    if isinstance(value, (int, str)):
        return Decimal(value)
    raise ValueError(f"Cannot convert {type(value).__name__} to Decimal: {value}")


def round_penny(amount: Decimal) -> Decimal:
    """Round to nearest cent using Banker's rounding (ROUND_HALF_EVEN)."""
    return amount.quantize(PENNY, rounding=ROUND_HALF_EVEN)


def rate_from_percent(percent: Decimal) -> Decimal:
    """Convert a percentage (e.g., 5 for 5%) to a decimal rate (0.05)."""
    return to_decimal(percent) / HUNDRED


def allocate_evenly(total: Decimal, periods: int) -> list[Decimal]:
    """
    Allocate a total amount evenly across periods using Banker's rounding.
    The last period absorbs any rounding difference (plug/stub).
    Guarantees sum of allocations == total exactly.
    """
    if periods <= 0:
        raise ValueError("periods must be positive")
    if periods == 1:
        return [round_penny(total)]

    per_period = round_penny(total / Decimal(periods))
    allocations = [per_period] * (periods - 1)

    # Plug: last period absorbs rounding difference
    allocated_so_far = per_period * Decimal(periods - 1)
    last_period = round_penny(total - allocated_so_far)
    allocations.append(last_period)

    return allocations
