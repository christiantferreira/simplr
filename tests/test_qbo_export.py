"""
Tests for QBO Journal Entry CSV Export Adapter.
"""

import pytest
from datetime import date
from decimal import Decimal

from execution.export.qbo_adapter import (
    QBOJournal, QBOJournalLine, format_qbo_date,
    build_prepaid_amortization_journal_qbo, build_prepaid_setup_journal_qbo,
    journals_to_csv_qbo, QBO_HEADERS,
)
from execution.calc.decimal_utils import ZERO


class TestQBODateFormat:
    def test_format_standard(self):
        assert format_qbo_date(date(2026, 3, 20)) == "03/20/2026"

    def test_format_single_digit(self):
        assert format_qbo_date(date(2026, 1, 5)) == "01/05/2026"

    def test_format_december(self):
        assert format_qbo_date(date(2026, 12, 31)) == "12/31/2026"


class TestQBOJournalBalance:
    def test_balanced_journal(self):
        journal = build_prepaid_amortization_journal_qbo(
            journal_no=1,
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1000"),
            description="Insurance prepaid amort",
            expense_account_name="Insurance Expense",
            asset_account_name="Prepaid Expenses",
        )
        assert journal.is_balanced()
        assert journal.total_debits() == Decimal("1000.00")
        assert journal.total_credits() == Decimal("1000.00")


class TestQBOCSVFormat:
    def test_headers(self):
        """QBO CSV must have correct headers."""
        expected = ["Journal No", "Journal Date", "Memo", "Account", "Debit", "Credit", "Description", "Name", "Class"]
        assert QBO_HEADERS == expected

    def test_csv_date_format(self):
        """QBO dates must be MM/DD/YYYY."""
        journal = build_prepaid_amortization_journal_qbo(
            journal_no=1,
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1000"),
            description="Test",
            expense_account_name="Insurance Expense",
            asset_account_name="Prepaid Expenses",
        )
        csv_content = journals_to_csv_qbo([journal])
        assert "03/31/2026" in csv_content

    def test_csv_debit_credit_columns(self):
        """QBO uses separate Debit and Credit columns."""
        journal = build_prepaid_amortization_journal_qbo(
            journal_no=1,
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1000"),
            description="Test",
            expense_account_name="Insurance Expense",
            asset_account_name="Prepaid Expenses",
        )
        csv_content = journals_to_csv_qbo([journal])
        lines = csv_content.strip().split("\n")

        # Line 1 = header, Line 2 = debit line, Line 3 = credit line
        # Debit line: has debit value, no credit value
        assert "1000.00" in lines[1]
        # Credit line: has credit value, no debit value
        assert "1000.00" in lines[2]

    def test_csv_uses_account_names(self):
        """QBO uses account NAMES, not codes."""
        journal = build_prepaid_amortization_journal_qbo(
            journal_no=1,
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1000"),
            description="Test",
            expense_account_name="Insurance Expense",
            asset_account_name="Prepaid Expenses",
        )
        csv_content = journals_to_csv_qbo([journal])
        assert "Insurance Expense" in csv_content
        assert "Prepaid Expenses" in csv_content

    def test_csv_with_class(self):
        """QBO Class included when provided."""
        journal = build_prepaid_amortization_journal_qbo(
            journal_no=1,
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1000"),
            description="Test",
            expense_account_name="Insurance Expense",
            asset_account_name="Prepaid Expenses",
            class_name="Marketing",
        )
        csv_content = journals_to_csv_qbo([journal])
        assert "Marketing" in csv_content

    def test_setup_journal_with_itc(self):
        """Setup JE with GST ITC: 3 lines balanced."""
        journal = build_prepaid_setup_journal_qbo(
            journal_no=1,
            setup_date=date(2026, 1, 1),
            prepaid_amount=Decimal("12000"),
            gst_hst_itc=Decimal("600"),
            description="Insurance",
            asset_account_name="Prepaid Expenses",
            cash_account_name="Cash",
            gst_receivable_account_name="GST Receivable",
        )
        assert len(journal.lines) == 3
        assert journal.is_balanced()
        assert journal.total_debits() == Decimal("12600.00")
        assert journal.total_credits() == Decimal("12600.00")

    def test_journal_numbering(self):
        """Multiple journals have distinct journal numbers."""
        j1 = build_prepaid_amortization_journal_qbo(
            journal_no=1,
            period_date=date(2026, 1, 31),
            amortization_amount=Decimal("1000"),
            description="Test",
            expense_account_name="Insurance Expense",
            asset_account_name="Prepaid Expenses",
        )
        j2 = build_prepaid_amortization_journal_qbo(
            journal_no=2,
            period_date=date(2026, 2, 28),
            amortization_amount=Decimal("1000"),
            description="Test",
            expense_account_name="Insurance Expense",
            asset_account_name="Prepaid Expenses",
        )
        csv_content = journals_to_csv_qbo([j1, j2])
        lines = csv_content.strip().split("\n")

        # Line 1 = header, Lines 2-3 = journal 1, Lines 4-5 = journal 2
        assert lines[1].startswith("1,")
        assert lines[3].startswith("2,")
