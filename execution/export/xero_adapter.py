"""
Xero Manual Journal CSV Export Adapter.

Generates CSV files in the exact format required by Xero's Manual Journal import.
"""

import csv
import io
import hashlib
from datetime import date, datetime
from decimal import Decimal
from dataclasses import dataclass, field

from ..calc.decimal_utils import ZERO, round_penny


XERO_DATE_FORMAT = "%d %b %Y"  # DD MMM YYYY — e.g., "31 Mar 2026"

XERO_HEADERS = [
    "*Narration",
    "*Date",
    "*Description",
    "*AccountCode",
    "*TaxRateName",
    "*Amount",
    "Reference",
    "TrackingName1",
    "TrackingOption1",
]


@dataclass
class XeroJournalLine:
    """A single line in a Xero Manual Journal."""
    narration: str
    date: date
    description: str
    account_code: str
    tax_rate_name: str
    amount: Decimal           # Positive = debit, negative = credit
    reference: str = ""
    tracking_name: str = ""
    tracking_option: str = ""


@dataclass
class XeroJournal:
    """A complete Xero Manual Journal (multiple lines that must balance to zero)."""
    lines: list[XeroJournalLine] = field(default_factory=list)

    def net_amount(self) -> Decimal:
        """Sum of all line amounts. Must be exactly zero for a valid journal."""
        return sum(line.amount for line in self.lines)

    def is_balanced(self) -> bool:
        """Check if debits equal credits."""
        return self.net_amount() == ZERO


def format_xero_date(d: date) -> str:
    """Format a date as DD MMM YYYY for Xero."""
    return d.strftime(XERO_DATE_FORMAT)


def generate_reference(module: str, year: int, month: int) -> str:
    """Generate a SIMPLR reference code. E.g., SIMPLR-PP-2026-03."""
    return f"SIMPLR-{module}-{year:04d}-{month:02d}"


def build_prepaid_amortization_journal(
    period_date: date,
    amortization_amount: Decimal,
    description: str,
    expense_account_code: str,
    asset_account_code: str,
    tax_rate_name: str,
    reference: str,
    tracking_name: str = "",
    tracking_option: str = "",
) -> XeroJournal:
    """
    Build a Xero journal for one month's prepaid amortization.
    DR Expense / CR Prepaid Asset.
    """
    narration = f"Prepaid Amortization - {period_date.strftime('%b %Y')}"
    amt = round_penny(amortization_amount)

    lines = [
        XeroJournalLine(
            narration=narration,
            date=period_date,
            description=description,
            account_code=expense_account_code,
            tax_rate_name=tax_rate_name,
            amount=amt,  # Positive = debit
            reference=reference,
            tracking_name=tracking_name,
            tracking_option=tracking_option,
        ),
        XeroJournalLine(
            narration=narration,
            date=period_date,
            description=description,
            account_code=asset_account_code,
            tax_rate_name=tax_rate_name,
            amount=-amt,  # Negative = credit
            reference=reference,
            tracking_name=tracking_name,
            tracking_option=tracking_option,
        ),
    ]

    return XeroJournal(lines=lines)


def build_prepaid_setup_journal(
    setup_date: date,
    prepaid_amount: Decimal,
    gst_hst_itc: Decimal,
    description: str,
    asset_account_code: str,
    cash_account_code: str,
    gst_receivable_account_code: str,
    tax_rate_name_asset: str,
    tax_rate_name_gst: str,
    reference: str,
    tracking_name: str = "",
    tracking_option: str = "",
) -> XeroJournal:
    """
    Build a Xero journal for the initial prepaid setup.
    DR Prepaid Asset (+ DR GST/HST Receivable if ITC) / CR Cash.
    """
    narration = f"Prepaid Setup - {description}"
    lines = []

    # DR Prepaid Asset
    lines.append(XeroJournalLine(
        narration=narration,
        date=setup_date,
        description=f"{description} - prepaid asset",
        account_code=asset_account_code,
        tax_rate_name=tax_rate_name_asset,
        amount=round_penny(prepaid_amount),
        reference=reference,
        tracking_name=tracking_name,
        tracking_option=tracking_option,
    ))

    # DR GST/HST Receivable (if ITC > 0)
    if gst_hst_itc > ZERO:
        lines.append(XeroJournalLine(
            narration=narration,
            date=setup_date,
            description=f"{description} - GST/HST ITC",
            account_code=gst_receivable_account_code,
            tax_rate_name=tax_rate_name_gst,
            amount=round_penny(gst_hst_itc),
            reference=reference,
            tracking_name=tracking_name,
            tracking_option=tracking_option,
        ))

    # CR Cash (total outflow)
    total_cash = round_penny(prepaid_amount + gst_hst_itc)
    lines.append(XeroJournalLine(
        narration=narration,
        date=setup_date,
        description=f"{description} - payment",
        account_code=cash_account_code,
        tax_rate_name=tax_rate_name_asset,
        amount=-total_cash,
        reference=reference,
        tracking_name=tracking_name,
        tracking_option=tracking_option,
    ))

    return XeroJournal(lines=lines)


def journals_to_csv(journals: list[XeroJournal]) -> str:
    """
    Convert a list of XeroJournals to a CSV string.
    UTF-8 without BOM. Decimal separator is always period.
    """
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    # Header with asterisk prefixes as required by Xero
    writer.writerow(XERO_HEADERS)

    for journal in journals:
        for line in journal.lines:
            writer.writerow([
                line.narration,
                format_xero_date(line.date),
                line.description,
                line.account_code,
                line.tax_rate_name,
                str(round_penny(line.amount)),
                line.reference,
                line.tracking_name,
                line.tracking_option,
            ])

    return output.getvalue()


def compute_export_hash(csv_content: str) -> str:
    """Compute SHA-256 hash of CSV content for export tracking."""
    return hashlib.sha256(csv_content.encode("utf-8")).hexdigest()


def generate_export_id(module: str, period_date: date) -> str:
    """Generate a unique export ID."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"EXP-{module}-{period_date.strftime('%Y%m')}-{ts}"
