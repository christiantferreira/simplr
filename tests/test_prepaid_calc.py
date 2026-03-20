"""
Tests for Prepaid Expenses Calculation Engine.
"""

import pytest
from datetime import date
from decimal import Decimal

from execution.calc.decimal_utils import to_decimal, round_penny, allocate_evenly, ZERO
from execution.calc.prepaid import (
    PrepaidInput, TaxConfig, calculate_prepaid, PrepaidResult,
)
from execution.calc.date_utils import (
    generate_amortization_periods, last_day_of_month, fiscal_year_dates,
)


class TestDecimalUtils:
    def test_to_decimal_from_string(self):
        assert to_decimal("12000") == Decimal("12000")

    def test_to_decimal_from_int(self):
        assert to_decimal(12000) == Decimal("12000")

    def test_to_decimal_from_float(self):
        # Float converted via string to avoid artifacts
        assert to_decimal(12000.50) == Decimal("12000.5")

    def test_round_penny(self):
        assert round_penny(Decimal("1000.005")) == Decimal("1000.00")  # Banker's: .005 -> .00
        assert round_penny(Decimal("1000.015")) == Decimal("1000.02")  # Banker's: .015 -> .02
        assert round_penny(Decimal("1000.125")) == Decimal("1000.12")  # Banker's: .125 -> .12
        assert round_penny(Decimal("1000.135")) == Decimal("1000.14")  # Banker's: .135 -> .14

    def test_allocate_evenly_exact(self):
        """$12,000 / 12 months = $1,000.00 each."""
        amounts = allocate_evenly(Decimal("12000"), 12)
        assert len(amounts) == 12
        assert all(a == Decimal("1000.00") for a in amounts)
        assert sum(amounts) == Decimal("12000.00")

    def test_allocate_evenly_with_remainder(self):
        """$10,000 / 3 = $3,333.33 + $3,333.33 + $3,333.34 (plug)."""
        amounts = allocate_evenly(Decimal("10000"), 3)
        assert len(amounts) == 3
        assert amounts[0] == Decimal("3333.33")
        assert amounts[1] == Decimal("3333.33")
        assert amounts[2] == Decimal("3333.34")  # Plug
        assert sum(amounts) == Decimal("10000.00")

    def test_allocate_evenly_single_period(self):
        amounts = allocate_evenly(Decimal("5000"), 1)
        assert amounts == [Decimal("5000.00")]


class TestDateUtils:
    def test_last_day_of_month(self):
        assert last_day_of_month(2026, 1) == date(2026, 1, 31)
        assert last_day_of_month(2026, 2) == date(2026, 2, 28)
        assert last_day_of_month(2024, 2) == date(2024, 2, 29)  # Leap year
        assert last_day_of_month(2026, 12) == date(2026, 12, 31)

    def test_generate_periods_full_year(self):
        """Jan 1 to Dec 31 = 12 full-month periods."""
        periods = generate_amortization_periods(
            date(2026, 1, 1), date(2026, 12, 31), mid_month_convention=False
        )
        assert len(periods) == 12
        assert periods[0]["month_end"] == date(2026, 1, 31)
        assert periods[11]["month_end"] == date(2026, 12, 31)
        assert all(p["fraction"] == Decimal("1") for p in periods)

    def test_generate_periods_mid_month(self):
        """Mar 15 to Mar 14 next year with mid-month = 12 periods, partial first/last."""
        periods = generate_amortization_periods(
            date(2026, 3, 15), date(2027, 3, 14), mid_month_convention=True
        )
        assert len(periods) == 13  # Mar 15-31, Apr-Feb (11 full), Mar 1-14
        # First month: 17 days out of 31
        assert periods[0]["fraction"] == Decimal("17") / Decimal("31")
        # Last month: 14 days out of 31
        assert periods[-1]["fraction"] == Decimal("14") / Decimal("31")

    def test_fiscal_year_dates_calendar(self):
        fy_start, fy_end = fiscal_year_dates(12, 31, date(2026, 6, 15))
        assert fy_start == date(2026, 1, 1)
        assert fy_end == date(2026, 12, 31)

    def test_fiscal_year_dates_march_end(self):
        fy_start, fy_end = fiscal_year_dates(3, 31, date(2026, 6, 15))
        assert fy_start == date(2026, 4, 1)
        assert fy_end == date(2027, 3, 31)


class TestPrepaidCalculation:
    def test_simple_12month(self):
        """$12,000 over 12 months = $1,000/month."""
        inp = PrepaidInput(
            description="Insurance",
            total_amount=Decimal("12000"),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            expense_account_code="6200",
            expense_account_name="Insurance Expense",
            asset_account_code="1400",
            asset_account_name="Prepaid Insurance",
        )
        result = calculate_prepaid(inp)

        assert result.capitalized_amount == Decimal("12000.00")
        assert result.gst_hst_itc_amount == ZERO
        assert len(result.schedule) == 12

        for line in result.schedule:
            assert line.amortization == Decimal("1000.00")

        assert result.schedule[0].opening_balance == Decimal("12000.00")
        assert result.schedule[0].ending_balance == Decimal("11000.00")
        assert result.schedule[-1].ending_balance == ZERO

    def test_mid_month_convention(self):
        """$12,000, starts Mar 15, ends Mar 14 next year with mid-month."""
        inp = PrepaidInput(
            description="Software License",
            total_amount=Decimal("12000"),
            start_date=date(2026, 3, 15),
            end_date=date(2027, 3, 14),
            expense_account_code="6300",
            expense_account_name="Software Expense",
            asset_account_code="1400",
            asset_account_name="Prepaid Software",
            mid_month_convention=True,
        )
        result = calculate_prepaid(inp)

        # Total amortization must equal capitalized amount exactly
        total_amort = sum(l.amortization for l in result.schedule)
        assert total_amort == Decimal("12000.00")

        # First month partial (17/31 of month)
        assert result.schedule[0].amortization < Decimal("1000.00")
        # Last month partial (14/31 of month)
        assert result.schedule[-1].is_plug is True

        # Ending balance must be zero
        assert result.schedule[-1].ending_balance == ZERO

    def test_pst_non_recoverable(self):
        """BC PST 7% non-recoverable: $12,000 + 7% = $12,840 capitalized."""
        inp = PrepaidInput(
            description="Insurance BC",
            total_amount=Decimal("12000"),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            expense_account_code="6200",
            expense_account_name="Insurance Expense",
            asset_account_code="1400",
            asset_account_name="Prepaid Insurance",
            tax_config=TaxConfig(
                pst_rate=Decimal("7"),
                pst_recoverable=False,
            ),
        )
        result = calculate_prepaid(inp)

        assert result.capitalized_amount == Decimal("12840.00")
        assert result.gst_hst_itc_amount == ZERO
        assert result.total_cash_outflow == Decimal("12840.00")

        # Monthly: $12,840 / 12 = $1,070.00
        for line in result.schedule:
            assert line.amortization == Decimal("1070.00")

        assert result.schedule[-1].ending_balance == ZERO

    def test_gst_recoverable(self):
        """GST 5% recoverable: $12,000 capitalized, $600 as ITC separate."""
        inp = PrepaidInput(
            description="Office Supplies",
            total_amount=Decimal("12000"),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            expense_account_code="6100",
            expense_account_name="Office Expense",
            asset_account_code="1400",
            asset_account_name="Prepaid Office Supplies",
            tax_config=TaxConfig(
                gst_hst_rate=Decimal("5"),
                gst_hst_recoverable=True,
            ),
        )
        result = calculate_prepaid(inp)

        assert result.capitalized_amount == Decimal("12000.00")
        assert result.gst_hst_itc_amount == Decimal("600.00")
        assert result.total_cash_outflow == Decimal("12600.00")

        # Monthly amort: $12,000 / 12 = $1,000
        for line in result.schedule:
            assert line.amortization == Decimal("1000.00")

    def test_gst_and_pst_bc(self):
        """BC: GST 5% recoverable + PST 7% non-recoverable."""
        inp = PrepaidInput(
            description="Insurance BC Full Tax",
            total_amount=Decimal("12000"),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            expense_account_code="6200",
            expense_account_name="Insurance Expense",
            asset_account_code="1400",
            asset_account_name="Prepaid Insurance",
            tax_config=TaxConfig(
                gst_hst_rate=Decimal("5"),
                gst_hst_recoverable=True,
                pst_rate=Decimal("7"),
                pst_recoverable=False,
            ),
        )
        result = calculate_prepaid(inp)

        # Capitalized: $12,000 + PST $840 = $12,840
        assert result.capitalized_amount == Decimal("12840.00")
        # ITC: GST $600
        assert result.gst_hst_itc_amount == Decimal("600.00")
        # Total cash: $12,840 + $600 = $13,440
        assert result.total_cash_outflow == Decimal("13440.00")

    def test_fx_rate(self):
        """USD contract at FX 1.35: $10,000 USD * 1.35 = $13,500 CAD."""
        inp = PrepaidInput(
            description="US Software License",
            total_amount=Decimal("10000"),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            expense_account_code="6300",
            expense_account_name="Software Expense",
            asset_account_code="1400",
            asset_account_name="Prepaid Software",
            fx_rate=Decimal("1.35"),
        )
        result = calculate_prepaid(inp)

        assert result.capitalized_amount == Decimal("13500.00")
        # Monthly: $13,500 / 12 = $1,125.00
        for line in result.schedule:
            assert line.amortization == Decimal("1125.00")

    def test_ending_balance_always_zero(self):
        """Regardless of amounts, ending balance must be exactly zero."""
        # Odd amount that doesn't divide evenly
        inp = PrepaidInput(
            description="Odd Amount",
            total_amount=Decimal("10000"),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            expense_account_code="6200",
            expense_account_name="Expense",
            asset_account_code="1400",
            asset_account_name="Prepaid",
        )
        result = calculate_prepaid(inp)

        assert result.schedule[-1].ending_balance == ZERO
        total = sum(l.amortization for l in result.schedule)
        assert total == Decimal("10000.00")

    def test_setup_je(self):
        """Setup JE should have correct amounts."""
        inp = PrepaidInput(
            description="Insurance",
            total_amount=Decimal("12000"),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            expense_account_code="6200",
            expense_account_name="Insurance Expense",
            asset_account_code="1400",
            asset_account_name="Prepaid Insurance",
            tax_config=TaxConfig(
                gst_hst_rate=Decimal("5"),
                gst_hst_recoverable=True,
            ),
        )
        result = calculate_prepaid(inp)

        assert result.setup_je.prepaid_amount == Decimal("12000.00")
        assert result.setup_je.gst_hst_itc == Decimal("600.00")
        assert result.setup_je.total_cash == Decimal("12600.00")

    def test_short_period(self):
        """3-month prepaid."""
        inp = PrepaidInput(
            description="Short Prepaid",
            total_amount=Decimal("3000"),
            start_date=date(2026, 4, 1),
            end_date=date(2026, 6, 30),
            expense_account_code="6200",
            expense_account_name="Expense",
            asset_account_code="1400",
            asset_account_name="Prepaid",
        )
        result = calculate_prepaid(inp)

        assert len(result.schedule) == 3
        for line in result.schedule:
            assert line.amortization == Decimal("1000.00")
        assert result.schedule[-1].ending_balance == ZERO
