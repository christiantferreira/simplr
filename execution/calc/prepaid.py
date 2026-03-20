"""
Prepaid Expenses Amortization Calculator.

Calculates linear amortization schedules for prepaid expenses
with support for mid-month convention, tax treatment (GST/HST ITC vs PST capitalized),
and FX rate conversion.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from .decimal_utils import (
    ZERO, ONE, HUNDRED, to_decimal, round_penny, rate_from_percent, allocate_evenly,
)
from .date_utils import generate_amortization_periods, last_day_of_month


@dataclass
class TaxConfig:
    """Tax configuration for a prepaid contract."""
    gst_hst_rate: Decimal = ZERO       # e.g., Decimal("5") for 5% GST
    gst_hst_recoverable: bool = True   # If True, GST/HST goes to ITC (not capitalized)
    pst_rate: Decimal = ZERO           # e.g., Decimal("7") for 7% PST BC
    pst_recoverable: bool = False      # PST is almost never recoverable in Canada


@dataclass
class PrepaidInput:
    """All inputs needed to calculate a prepaid amortization schedule."""
    description: str
    total_amount: Decimal               # Pre-tax amount
    start_date: date
    end_date: date
    expense_account_code: str           # DR account for monthly amort
    expense_account_name: str
    asset_account_code: str             # CR account (prepaid asset)
    asset_account_name: str
    tax_config: TaxConfig = field(default_factory=TaxConfig)
    mid_month_convention: bool = False
    fx_rate: Decimal = ONE              # FX rate at inception (1.0 = CAD)
    fiscal_year_end_month: int = 12
    fiscal_year_end_day: int = 31
    tracking_name: str = ""             # Xero Tracking Category name
    tracking_option: str = ""           # Xero Tracking Category option
    client_name: str = ""
    xero_tax_rate_name: str = "Tax Exempt"  # Default TaxRateName for Xero export


@dataclass
class PrepaidScheduleLine:
    """One period in the amortization schedule."""
    period_date: date          # Month-end date (JE posting date)
    period_start: date
    period_end: date
    amortization: Decimal      # Amount amortized this period
    opening_balance: Decimal   # Balance at start of period
    ending_balance: Decimal    # Balance at end of period
    fraction: Decimal          # Fraction of full month (1.0 = full)
    is_plug: bool = False      # True if this is the last period (plug adjustment)


@dataclass
class PrepaidSetupJE:
    """The initial journal entry to record the prepaid."""
    date: date
    prepaid_amount: Decimal     # Amount capitalized as prepaid asset (includes non-recoverable PST)
    gst_hst_itc: Decimal        # GST/HST ITC amount (if recoverable)
    total_cash: Decimal         # Total cash outflow (prepaid + ITC)
    description: str


@dataclass
class PrepaidResult:
    """Complete result of a prepaid amortization calculation."""
    input: PrepaidInput
    capitalized_amount: Decimal         # Amount on balance sheet (after PST, FX)
    gst_hst_itc_amount: Decimal         # Separate ITC amount
    total_cash_outflow: Decimal         # Total paid
    schedule: list[PrepaidScheduleLine]
    setup_je: PrepaidSetupJE


def calculate_prepaid(inp: PrepaidInput) -> PrepaidResult:
    """
    Calculate a complete prepaid amortization schedule.

    Steps:
    1. Apply FX rate to convert to CAD
    2. Calculate tax amounts (PST capitalized, GST/HST as ITC)
    3. Determine capitalized amount
    4. Generate periods (with mid-month convention if enabled)
    5. Allocate amortization across periods (plug last period)
    """
    # Step 1: Apply FX rate
    base_amount_cad = round_penny(to_decimal(inp.total_amount) * to_decimal(inp.fx_rate))

    # Step 2: Calculate tax
    tax = inp.tax_config
    gst_hst_amount = ZERO
    pst_amount = ZERO

    if tax.gst_hst_rate > ZERO:
        gst_hst_amount = round_penny(base_amount_cad * rate_from_percent(tax.gst_hst_rate))

    if tax.pst_rate > ZERO:
        pst_amount = round_penny(base_amount_cad * rate_from_percent(tax.pst_rate))

    # Step 3: Determine capitalized amount
    # PST non-recoverable = capitalized into prepaid value
    # GST/HST recoverable = separate ITC, not capitalized
    capitalized = base_amount_cad
    gst_hst_itc = ZERO

    if tax.pst_rate > ZERO and not tax.pst_recoverable:
        capitalized = capitalized + pst_amount

    if tax.gst_hst_rate > ZERO and tax.gst_hst_recoverable:
        gst_hst_itc = gst_hst_amount
    elif tax.gst_hst_rate > ZERO and not tax.gst_hst_recoverable:
        capitalized = capitalized + gst_hst_amount

    total_cash = capitalized + gst_hst_itc

    # Step 4: Generate periods
    periods = generate_amortization_periods(
        inp.start_date, inp.end_date, inp.mid_month_convention
    )

    if not periods:
        raise ValueError("No amortization periods generated. Check start/end dates.")

    # Step 5: Allocate amortization
    schedule_lines = _allocate_amortization(capitalized, periods, inp.mid_month_convention)

    # Step 6: Build setup JE
    setup_je = PrepaidSetupJE(
        date=inp.start_date,
        prepaid_amount=capitalized,
        gst_hst_itc=gst_hst_itc,
        total_cash=total_cash,
        description=f"Prepaid setup - {inp.description}",
    )

    return PrepaidResult(
        input=inp,
        capitalized_amount=capitalized,
        gst_hst_itc_amount=gst_hst_itc,
        total_cash_outflow=total_cash,
        schedule=schedule_lines,
        setup_je=setup_je,
    )


def _allocate_amortization(
    total: Decimal,
    periods: list[dict],
    mid_month: bool,
) -> list[PrepaidScheduleLine]:
    """
    Allocate the total capitalized amount across amortization periods.

    If mid_month is True: weight allocation by each period's fraction.
    If mid_month is False: equal allocation with plug on last period.
    """
    num_periods = len(periods)

    if mid_month:
        # Weighted allocation based on day fractions
        total_fraction = sum(p["fraction"] for p in periods)
        raw_amounts = []
        for p in periods:
            weight = p["fraction"] / total_fraction
            raw_amounts.append(round_penny(total * weight))

        # Plug: adjust last period so total is exact
        allocated = sum(raw_amounts[:-1])
        raw_amounts[-1] = round_penny(total - allocated)
        amounts = raw_amounts
    else:
        # Even allocation with plug
        amounts = allocate_evenly(total, num_periods)

    # Build schedule lines
    lines = []
    balance = total

    for i, (period, amount) in enumerate(zip(periods, amounts)):
        opening = balance
        ending = round_penny(balance - amount)
        is_last = (i == num_periods - 1)

        # Safety: if last period, ensure ending balance is exactly zero
        if is_last:
            amount = opening
            ending = ZERO

        lines.append(PrepaidScheduleLine(
            period_date=period["month_end"],
            period_start=period["period_start"],
            period_end=period["period_end"],
            amortization=amount,
            opening_balance=opening,
            ending_balance=ending,
            fraction=period["fraction"],
            is_plug=is_last,
        ))
        balance = ending

    return lines
