"""
Pre-Export Validation for Simplr.

Validates journal entries before generating CSV exports.
Catches errors that would cause Xero/QBO import failures.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from ..calc.decimal_utils import ZERO, round_penny
from ..export.xero_adapter import XeroJournal
from ..export.qbo_adapter import QBOJournal


@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: str       # "error" or "warning"
    code: str           # Machine-readable code
    message: str        # Human-readable message
    field: str = ""     # Which field has the issue


@dataclass
class ValidationResult:
    """Result of pre-export validation."""
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def validate_xero_journals(
    journals: list[XeroJournal],
    configured_account_codes: list[str],
    configured_tax_rate_names: list[str],
    open_periods: list[str],           # List of "YYYY-MM" strings
    exported_periods: list[str],       # Previously exported "YYYY-MM" strings
    require_tracking: bool = False,
) -> ValidationResult:
    """
    Validate Xero journals before export.

    Checks:
    1. Each journal is balanced (debits = credits)
    2. Account codes exist in configured COA
    3. TaxRateName matches configured mapping (CASE-SENSITIVE)
    4. Date is within an open period
    5. Warning if period was already exported
    6. Tracking categories present if required
    """
    issues = []

    for idx, journal in enumerate(journals):
        j_label = f"Journal #{idx + 1}"

        # Check 1: Balanced
        net = journal.net_amount()
        if net != ZERO:
            issues.append(ValidationIssue(
                severity="error",
                code="UNBALANCED",
                message=f"{j_label}: Debits and credits do not balance. Net amount: {net}",
                field="*Amount",
            ))

        for line_idx, line in enumerate(journal.lines):
            l_label = f"{j_label}, Line #{line_idx + 1}"

            # Check 2: Account code exists
            if configured_account_codes and line.account_code not in configured_account_codes:
                issues.append(ValidationIssue(
                    severity="error",
                    code="INVALID_ACCOUNT",
                    message=f"{l_label}: Account code '{line.account_code}' not found in Chart of Accounts",
                    field="*AccountCode",
                ))

            # Check 3: TaxRateName (case-sensitive)
            if configured_tax_rate_names and line.tax_rate_name not in configured_tax_rate_names:
                issues.append(ValidationIssue(
                    severity="error",
                    code="INVALID_TAX_RATE",
                    message=(
                        f"{l_label}: TaxRateName '{line.tax_rate_name}' not in configured mappings. "
                        f"Available: {configured_tax_rate_names}. Note: this is CASE-SENSITIVE."
                    ),
                    field="*TaxRateName",
                ))

            # Check 4: Date in open period
            period_key = line.date.strftime("%Y-%m")
            if open_periods and period_key not in open_periods:
                issues.append(ValidationIssue(
                    severity="error",
                    code="PERIOD_CLOSED",
                    message=f"{l_label}: Period {period_key} is not open. JE date: {line.date}",
                    field="*Date",
                ))

            # Check 5: Already exported
            if period_key in exported_periods:
                issues.append(ValidationIssue(
                    severity="warning",
                    code="ALREADY_EXPORTED",
                    message=f"{l_label}: Period {period_key} was previously exported. Possible duplication.",
                    field="*Date",
                ))

            # Check 6: Tracking required
            if require_tracking and (not line.tracking_name or not line.tracking_option):
                issues.append(ValidationIssue(
                    severity="error",
                    code="MISSING_TRACKING",
                    message=f"{l_label}: Tracking category is required but not set",
                    field="TrackingName1",
                ))

    has_errors = any(i.severity == "error" for i in issues)
    return ValidationResult(is_valid=not has_errors, issues=issues)


def validate_qbo_journals(
    journals: list[QBOJournal],
    configured_account_names: list[str],
    open_periods: list[str],
    exported_periods: list[str],
    require_class: bool = False,
) -> ValidationResult:
    """
    Validate QBO journals before export.

    Checks:
    1. Each journal is balanced (debits = credits)
    2. Account names exist in configured COA
    3. Date is within an open period
    4. Warning if period was already exported
    5. Class present if required
    """
    issues = []

    for idx, journal in enumerate(journals):
        j_label = f"Journal #{idx + 1}"

        # Check 1: Balanced
        if not journal.is_balanced():
            diff = journal.total_debits() - journal.total_credits()
            issues.append(ValidationIssue(
                severity="error",
                code="UNBALANCED",
                message=f"{j_label}: Debits ({journal.total_debits()}) != Credits ({journal.total_credits()}). Diff: {diff}",
                field="Debit/Credit",
            ))

        for line_idx, line in enumerate(journal.lines):
            l_label = f"{j_label}, Line #{line_idx + 1}"

            # Check 2: Account name exists
            if configured_account_names and line.account not in configured_account_names:
                issues.append(ValidationIssue(
                    severity="error",
                    code="INVALID_ACCOUNT",
                    message=f"{l_label}: Account '{line.account}' not found in Chart of Accounts",
                    field="Account",
                ))

            # Check 3: Date in open period
            period_key = line.journal_date.strftime("%Y-%m")
            if open_periods and period_key not in open_periods:
                issues.append(ValidationIssue(
                    severity="error",
                    code="PERIOD_CLOSED",
                    message=f"{l_label}: Period {period_key} is not open",
                    field="Journal Date",
                ))

            # Check 4: Already exported
            if period_key in exported_periods:
                issues.append(ValidationIssue(
                    severity="warning",
                    code="ALREADY_EXPORTED",
                    message=f"{l_label}: Period {period_key} was previously exported. Possible duplication.",
                    field="Journal Date",
                ))

            # Check 5: Class required
            if require_class and not line.class_name:
                issues.append(ValidationIssue(
                    severity="error",
                    code="MISSING_CLASS",
                    message=f"{l_label}: Class is required but not set",
                    field="Class",
                ))

    has_errors = any(i.severity == "error" for i in issues)
    return ValidationResult(is_valid=not has_errors, issues=issues)
