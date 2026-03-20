"""
Tests for Roll-Forward Working Paper Report.
"""

import pytest
from datetime import date
from decimal import Decimal

from execution.calc.decimal_utils import ZERO, round_penny
from execution.calc.prepaid import PrepaidInput, TaxConfig, calculate_prepaid
from execution.reports.roll_forward import generate_roll_forward, report_to_dict


class TestRollForward:
    def _make_insurance_result(self):
        """Helper: $12,000 insurance over 12 months starting Jan 1."""
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
        return calculate_prepaid(inp)

    def _make_software_result(self):
        """Helper: $6,000 software over 12 months starting Jan 1."""
        inp = PrepaidInput(
            description="Software",
            total_amount=Decimal("6000"),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            expense_account_code="6300",
            expense_account_name="Software Expense",
            asset_account_code="1400",
            asset_account_name="Prepaid Software",
        )
        return calculate_prepaid(inp)

    def test_q1_roll_forward(self):
        """Q1 roll-forward: opening $18,000 + $0 additions - $4,500 amort = $13,500 ending."""
        insurance = self._make_insurance_result()
        software = self._make_software_result()

        report = generate_roll_forward(
            results=[insurance, software],
            period_start=date(2026, 1, 1),
            period_end=date(2026, 3, 31),
            client_name="Test Client",
        )

        # These contracts start on Jan 1, so in Q1 they are additions
        # Opening = 0 (contracts start this period), Additions = 18000
        assert report.total_additions == Decimal("18000.00")
        assert report.total_amortization == Decimal("4500.00")
        assert report.total_ending == Decimal("13500.00")

        # Verify: opening + additions - amortization = ending (to the penny)
        computed = round_penny(
            report.total_opening + report.total_additions - report.total_amortization
        )
        assert computed == report.total_ending

    def test_mid_year_roll_forward(self):
        """Q2 roll-forward: opening balance from end of Q1."""
        insurance = self._make_insurance_result()

        report = generate_roll_forward(
            results=[insurance],
            period_start=date(2026, 4, 1),
            period_end=date(2026, 6, 30),
            client_name="Test Client",
        )

        # Opening = $12,000 - 3 months * $1,000 = $9,000
        assert report.total_opening == Decimal("9000.00")
        assert report.total_additions == ZERO
        assert report.total_amortization == Decimal("3000.00")
        assert report.total_ending == Decimal("6000.00")

        # Verify equation
        computed = round_penny(
            report.total_opening + report.total_additions - report.total_amortization
        )
        assert computed == report.total_ending

    def test_next_je_info(self):
        """Report should show next JE amount and month."""
        insurance = self._make_insurance_result()

        report = generate_roll_forward(
            results=[insurance],
            period_start=date(2026, 1, 1),
            period_end=date(2026, 3, 31),
        )

        line = report.lines[0]
        assert line.next_je_amount == Decimal("1000.00")
        assert line.next_je_month == "Apr 2026"

    def test_fully_amortized_contract(self):
        """Contract fully amortized before report period shows nothing."""
        insurance = self._make_insurance_result()

        report = generate_roll_forward(
            results=[insurance],
            period_start=date(2027, 1, 1),
            period_end=date(2027, 3, 31),
        )

        # No data for this contract in 2027
        assert len(report.lines) == 1
        assert report.total_opening == ZERO
        assert report.total_ending == ZERO

    def test_report_to_dict(self):
        """Verify dict conversion for XLSX export."""
        insurance = self._make_insurance_result()

        report = generate_roll_forward(
            results=[insurance],
            period_start=date(2026, 4, 1),
            period_end=date(2026, 6, 30),
        )
        d = report_to_dict(report)

        assert "contracts" in d
        assert "totals" in d
        assert len(d["contracts"]) == 1
        assert d["totals"]["opening_balance"] == Decimal("9000.00")
        assert d["totals"]["ending_balance"] == Decimal("6000.00")

    def test_multiple_contracts_totals(self):
        """Multiple contracts: totals must add up correctly."""
        insurance = self._make_insurance_result()
        software = self._make_software_result()

        report = generate_roll_forward(
            results=[insurance, software],
            period_start=date(2026, 4, 1),
            period_end=date(2026, 6, 30),
            client_name="Multi-Contract Client",
        )

        # Insurance: opening 9000, amort 3000, ending 6000
        # Software: opening 4500, amort 1500, ending 3000
        assert report.total_opening == Decimal("13500.00")
        assert report.total_amortization == Decimal("4500.00")
        assert report.total_ending == Decimal("9000.00")

        # Verify equation
        computed = round_penny(
            report.total_opening + report.total_additions - report.total_amortization
        )
        assert computed == report.total_ending
