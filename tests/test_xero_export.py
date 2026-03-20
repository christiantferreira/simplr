"""
Tests for Xero Manual Journal CSV Export Adapter.
"""

import pytest
from datetime import date
from decimal import Decimal

from execution.export.xero_adapter import (
    XeroJournal, XeroJournalLine, format_xero_date, generate_reference,
    build_prepaid_amortization_journal, build_prepaid_setup_journal,
    journals_to_csv, compute_export_hash, XERO_HEADERS,
)
from execution.calc.decimal_utils import ZERO


class TestXeroDateFormat:
    def test_format_standard(self):
        assert format_xero_date(date(2026, 3, 31)) == "31 Mar 2026"

    def test_format_single_digit_day(self):
        assert format_xero_date(date(2026, 1, 5)) == "05 Jan 2026"

    def test_format_december(self):
        assert format_xero_date(date(2026, 12, 31)) == "31 Dec 2026"

    def test_never_mm_dd_yyyy(self):
        """Xero date must NEVER be in MM/DD/YYYY format."""
        result = format_xero_date(date(2026, 3, 10))
        assert "/" not in result
        assert result == "10 Mar 2026"


class TestXeroReference:
    def test_prepaid_reference(self):
        assert generate_reference("PP", 2026, 3) == "SIMPLR-PP-2026-03"

    def test_reference_padding(self):
        assert generate_reference("PP", 2026, 1) == "SIMPLR-PP-2026-01"


class TestXeroJournalBalance:
    def test_balanced_journal(self):
        journal = build_prepaid_amortization_journal(
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1000"),
            description="Insurance prepaid amort",
            expense_account_code="6200",
            asset_account_code="1400",
            tax_rate_name="Tax Exempt",
            reference="SIMPLR-PP-2026-03",
        )
        assert journal.is_balanced()
        assert journal.net_amount() == ZERO

    def test_unbalanced_journal(self):
        journal = XeroJournal(lines=[
            XeroJournalLine(
                narration="Test",
                date=date(2026, 1, 31),
                description="Test",
                account_code="6200",
                tax_rate_name="Tax Exempt",
                amount=Decimal("1000.00"),
            ),
        ])
        assert not journal.is_balanced()


class TestXeroCSVFormat:
    def test_headers_have_asterisks(self):
        """Xero requires asterisk prefix on required fields."""
        required_headers = ["*Narration", "*Date", "*Description", "*AccountCode", "*TaxRateName", "*Amount"]
        for h in required_headers:
            assert h in XERO_HEADERS

    def test_csv_encoding(self):
        """CSV must be UTF-8 without BOM."""
        journal = build_prepaid_amortization_journal(
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1000"),
            description="Insurance prepaid amort",
            expense_account_code="6200",
            asset_account_code="1400",
            tax_rate_name="Tax Exempt",
            reference="SIMPLR-PP-2026-03",
        )
        csv_content = journals_to_csv([journal])

        # No BOM
        assert not csv_content.startswith("\ufeff")

        # Encoding check — should be valid UTF-8
        csv_bytes = csv_content.encode("utf-8")
        assert csv_bytes.decode("utf-8") == csv_content

    def test_csv_date_format(self):
        """Dates in CSV must be DD MMM YYYY."""
        journal = build_prepaid_amortization_journal(
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1000"),
            description="Test",
            expense_account_code="6200",
            asset_account_code="1400",
            tax_rate_name="Tax Exempt",
            reference="TEST",
        )
        csv_content = journals_to_csv([journal])

        assert "31 Mar 2026" in csv_content
        # Must NOT contain MM/DD/YYYY
        assert "03/31/2026" not in csv_content

    def test_csv_amount_signs(self):
        """Positive = debit, Negative = credit."""
        journal = build_prepaid_amortization_journal(
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1000"),
            description="Test",
            expense_account_code="6200",
            asset_account_code="1400",
            tax_rate_name="Tax Exempt",
            reference="TEST",
        )
        csv_content = journals_to_csv([journal])
        lines = csv_content.strip().split("\n")

        # Line 1 = header, Line 2 = debit, Line 3 = credit
        assert "1000.00" in lines[1]    # Debit (positive)
        assert "-1000.00" in lines[2]   # Credit (negative)

    def test_csv_decimal_separator(self):
        """Decimal separator must always be period, never comma."""
        journal = build_prepaid_amortization_journal(
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1234.56"),
            description="Test",
            expense_account_code="6200",
            asset_account_code="1400",
            tax_rate_name="Tax Exempt",
            reference="TEST",
        )
        csv_content = journals_to_csv([journal])

        # Amount field should have period decimal
        assert "1234.56" in csv_content

    def test_csv_tax_rate_name_preserved(self):
        """TaxRateName must be exact case-sensitive string."""
        journal = build_prepaid_amortization_journal(
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1000"),
            description="Test",
            expense_account_code="6200",
            asset_account_code="1400",
            tax_rate_name="GST on Expenses",
            reference="TEST",
        )
        csv_content = journals_to_csv([journal])
        assert "GST on Expenses" in csv_content

    def test_csv_with_tracking(self):
        """TrackingName1 and TrackingOption1 included when provided."""
        journal = build_prepaid_amortization_journal(
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1000"),
            description="Test",
            expense_account_code="6200",
            asset_account_code="1400",
            tax_rate_name="Tax Exempt",
            reference="TEST",
            tracking_name="Department",
            tracking_option="Marketing",
        )
        csv_content = journals_to_csv([journal])
        assert "Department" in csv_content
        assert "Marketing" in csv_content

    def test_setup_journal_with_itc(self):
        """Setup JE with GST ITC: 3 lines (asset + ITC + cash)."""
        journal = build_prepaid_setup_journal(
            setup_date=date(2026, 1, 1),
            prepaid_amount=Decimal("12000"),
            gst_hst_itc=Decimal("600"),
            description="Insurance",
            asset_account_code="1400",
            cash_account_code="1000",
            gst_receivable_account_code="1200",
            tax_rate_name_asset="Tax Exempt",
            tax_rate_name_gst="GST on Expenses",
            reference="SIMPLR-PP-2026-01",
        )
        assert len(journal.lines) == 3
        assert journal.is_balanced()

        # DR Prepaid 12000 + DR GST 600 + CR Cash -12600 = 0
        amounts = [l.amount for l in journal.lines]
        assert sum(amounts) == ZERO

    def test_export_hash_deterministic(self):
        """Same CSV content produces same hash."""
        journal = build_prepaid_amortization_journal(
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1000"),
            description="Test",
            expense_account_code="6200",
            asset_account_code="1400",
            tax_rate_name="Tax Exempt",
            reference="TEST",
        )
        csv1 = journals_to_csv([journal])
        csv2 = journals_to_csv([journal])
        assert compute_export_hash(csv1) == compute_export_hash(csv2)

    def test_full_xero_csv_format(self):
        """Verify complete CSV matches expected Xero import format."""
        journal = build_prepaid_amortization_journal(
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1000"),
            description="Insurance prepaid amort",
            expense_account_code="6200",
            asset_account_code="1400",
            tax_rate_name="Tax Exempt",
            reference="SIMPLR-PP-2026-03",
        )
        csv_content = journals_to_csv([journal])
        lines = csv_content.strip().split("\n")

        # Header line
        assert lines[0] == "*Narration,*Date,*Description,*AccountCode,*TaxRateName,*Amount,Reference,TrackingName1,TrackingOption1"

        # Data lines
        assert len(lines) == 3  # header + 2 data lines
