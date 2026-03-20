"""
Date utilities for Simplr.
Handles fiscal year calculations, mid-month convention, and period generation.
"""

import calendar
from datetime import date, timedelta
from decimal import Decimal

from .decimal_utils import to_decimal, round_penny, ZERO


def last_day_of_month(year: int, month: int) -> date:
    """Return the last calendar day of the given month."""
    day = calendar.monthrange(year, month)[1]
    return date(year, month, day)


def months_between(start: date, end: date) -> int:
    """
    Count the number of full or partial months between start and end (inclusive).
    E.g., Jan 1 to Dec 31 = 12 months. Mar 15 to Mar 14 next year = 12 months.
    """
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day >= start.day:
        months += 1
    else:
        months += 1
    return max(months, 1)


def generate_amortization_periods(
    start_date: date,
    end_date: date,
    mid_month_convention: bool = False,
) -> list[dict]:
    """
    Generate amortization periods from start_date to end_date.

    Each period is a dict with:
        - period_start: first day of the amortization period
        - period_end: last day of the amortization period
        - month_end: the month-end date (for JE posting)
        - fraction: Decimal fraction of the full month (1.0 for full, <1.0 for partial)

    If mid_month_convention is True:
        - First month gets a partial fraction based on remaining days / total days
        - Last month gets a partial fraction based on elapsed days / total days
    If mid_month_convention is False:
        - All months are treated as full months (fraction = 1.0)
        - The number of periods = months between start and end
    """
    periods = []

    if start_date > end_date:
        raise ValueError(f"start_date ({start_date}) must be <= end_date ({end_date})")

    current = start_date
    while current <= end_date:
        month_start = date(current.year, current.month, 1)
        month_last = last_day_of_month(current.year, current.month)

        period_start = max(current, month_start)
        period_end = min(end_date, month_last)

        total_days_in_month = Decimal(str(month_last.day))

        if mid_month_convention:
            days_in_period = Decimal(str((period_end - period_start).days + 1))
            fraction = days_in_period / total_days_in_month
        else:
            fraction = Decimal("1")

        periods.append({
            "period_start": period_start,
            "period_end": period_end,
            "month_end": month_last,
            "fraction": fraction,
        })

        # Move to first day of next month
        if month_last.month == 12:
            current = date(month_last.year + 1, 1, 1)
        else:
            current = date(month_last.year, month_last.month + 1, 1)

    return periods


def fiscal_year_dates(fiscal_year_end_month: int, fiscal_year_end_day: int, target_date: date) -> tuple[date, date]:
    """
    Return (fy_start, fy_end) for the fiscal year containing target_date.

    fiscal_year_end_month/day: e.g., 12/31 for calendar year, 3/31 for March FYE.
    """
    fy_end_this_year = date(target_date.year, fiscal_year_end_month, fiscal_year_end_day)

    if target_date <= fy_end_this_year:
        fy_end = fy_end_this_year
    else:
        if fiscal_year_end_month == 12 and fiscal_year_end_day == 31:
            fy_end = date(target_date.year + 1, 12, 31)
        else:
            fy_end = date(target_date.year + 1, fiscal_year_end_month, fiscal_year_end_day)

    # FY start = day after previous FY end
    if fy_end.month == fiscal_year_end_month and fy_end.day == fiscal_year_end_day:
        prev_fy_end = date(fy_end.year - 1, fiscal_year_end_month, fiscal_year_end_day)
    else:
        prev_fy_end = date(fy_end.year - 1, fiscal_year_end_month, fiscal_year_end_day)

    fy_start = prev_fy_end + timedelta(days=1)

    return fy_start, fy_end


def count_full_months(start_date: date, end_date: date) -> int:
    """
    Count the number of periods for amortization without mid-month convention.
    This is simply the number of months from start to end, inclusive of both endpoints.
    """
    if start_date.day == 1:
        # Starts on first of month — full months
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
    else:
        # Partial first month counts as one period
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
    return max(months, 1)
