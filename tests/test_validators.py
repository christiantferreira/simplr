"""
Tests for Pre-Export Validation.
"""

import pytest
from datetime import date
from decimal import Decimal

from execution.export.xero_adapter import (
    XeroJournal, XeroJournalLine, build_prepaid_amortization_journal,
)
from execution.export.qbo_adapter import (
    build_prepaid_amortization_journal_qbo,
)
from execution.validators.pre_export import (
    validate_xero_journals, validate_qbo_journals,
)
from execution.calc.decimal_utils import ZERO


class TestXeroValidation:
    def _valid_journal(self):
        return build_prepaid_amortization_journal(
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1000"),
            description="Insurance prepaid amort",
            expense_account_code="6200",
            asset_account_code="1400",
            tax_rate_name="Tax Exempt",
            reference="SIMPLR-PP-2026-03",
        )

    def test_valid_passes(self):
        journal = self._valid_journal()
        result = validate_xero_journals(
            journals=[journal],
            configured_account_codes=["6200", "1400"],
            configured_tax_rate_names=["Tax Exempt"],
            open_periods=["2026-03"],
            exported_periods=[],
        )
        assert result.is_valid
        assert len(result.errors) == 0

    def test_catches_missing_account(self):
        journal = self._valid_journal()
        result = validate_xero_journals(
            journals=[journal],
            configured_account_codes=["6200"],  # Missing 1400
            configured_tax_rate_names=["Tax Exempt"],
            open_periods=["2026-03"],
            exported_periods=[],
        )
        assert not result.is_valid
        assert any(i.code == "INVALID_ACCOUNT" for i in result.errors)

    def test_catches_wrong_tax_rate_name(self):
        """TaxRateName is CASE-SENSITIVE."""
        journal = self._valid_journal()
        result = validate_xero_journals(
            journals=[journal],
            configured_account_codes=["6200", "1400"],
            configured_tax_rate_names=["Tax exempt"],  # Wrong case!
            open_periods=["2026-03"],
            exported_periods=[],
        )
        assert not result.is_valid
        assert any(i.code == "INVALID_TAX_RATE" for i in result.errors)

    def test_catches_unbalanced_journal(self):
        journal = XeroJournal(lines=[
            XeroJournalLine(
                narration="Test", date=date(2026, 3, 31),
                description="Test", account_code="6200",
                tax_rate_name="Tax Exempt", amount=Decimal("1000.00"),
            ),
            XeroJournalLine(
                narration="Test", date=date(2026, 3, 31),
                description="Test", account_code="1400",
                tax_rate_name="Tax Exempt", amount=Decimal("-999.99"),
            ),
        ])
        result = validate_xero_journals(
            journals=[journal],
            configured_account_codes=["6200", "1400"],
            configured_tax_rate_names=["Tax Exempt"],
            open_periods=["2026-03"],
            exported_periods=[],
        )
        assert not result.is_valid
        assert any(i.code == "UNBALANCED" for i in result.errors)

    def test_catches_closed_period(self):
        journal = self._valid_journal()
        result = validate_xero_journals(
            journals=[journal],
            configured_account_codes=["6200", "1400"],
            configured_tax_rate_names=["Tax Exempt"],
            open_periods=["2026-04"],  # March not open
            exported_periods=[],
        )
        assert not result.is_valid
        assert any(i.code == "PERIOD_CLOSED" for i in result.errors)

    def test_warns_already_exported(self):
        journal = self._valid_journal()
        result = validate_xero_journals(
            journals=[journal],
            configured_account_codes=["6200", "1400"],
            configured_tax_rate_names=["Tax Exempt"],
            open_periods=["2026-03"],
            exported_periods=["2026-03"],  # Already exported!
        )
        assert result.is_valid  # Warnings don't block
        assert len(result.warnings) > 0
        assert any(i.code == "ALREADY_EXPORTED" for i in result.warnings)

    def test_catches_missing_tracking(self):
        journal = self._valid_journal()
        result = validate_xero_journals(
            journals=[journal],
            configured_account_codes=["6200", "1400"],
            configured_tax_rate_names=["Tax Exempt"],
            open_periods=["2026-03"],
            exported_periods=[],
            require_tracking=True,
        )
        assert not result.is_valid
        assert any(i.code == "MISSING_TRACKING" for i in result.errors)

    def test_empty_config_skips_checks(self):
        """If no COA/tax configured, skip those checks (first-time setup)."""
        journal = self._valid_journal()
        result = validate_xero_journals(
            journals=[journal],
            configured_account_codes=[],
            configured_tax_rate_names=[],
            open_periods=[],
            exported_periods=[],
        )
        assert result.is_valid


class TestQBOValidation:
    def _valid_journal(self):
        return build_prepaid_amortization_journal_qbo(
            journal_no=1,
            period_date=date(2026, 3, 31),
            amortization_amount=Decimal("1000"),
            description="Insurance prepaid amort",
            expense_account_name="Insurance Expense",
            asset_account_name="Prepaid Expenses",
        )

    def test_valid_passes(self):
        journal = self._valid_journal()
        result = validate_qbo_journals(
            journals=[journal],
            configured_account_names=["Insurance Expense", "Prepaid Expenses"],
            open_periods=["2026-03"],
            exported_periods=[],
        )
        assert result.is_valid

    def test_catches_missing_account(self):
        journal = self._valid_journal()
        result = validate_qbo_journals(
            journals=[journal],
            configured_account_names=["Insurance Expense"],  # Missing "Prepaid Expenses"
            open_periods=["2026-03"],
            exported_periods=[],
        )
        assert not result.is_valid
        assert any(i.code == "INVALID_ACCOUNT" for i in result.errors)

    def test_catches_missing_class(self):
        journal = self._valid_journal()
        result = validate_qbo_journals(
            journals=[journal],
            configured_account_names=["Insurance Expense", "Prepaid Expenses"],
            open_periods=["2026-03"],
            exported_periods=[],
            require_class=True,
        )
        assert not result.is_valid
        assert any(i.code == "MISSING_CLASS" for i in result.errors)
