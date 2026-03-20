"""
QuickBooks Online (QBO) Journal Entry CSV Export Adapter.

Generates CSV files in QBO's native Journal Entry import format.
NOT IIF format (legacy/obsolete).
"""

import csv
import io
from datetime import date
from decimal import Decimal
from dataclasses import dataclass, field

from ..calc.decimal_utils import ZERO, round_penny


QBO_DATE_FORMAT = "%m/%d/%Y"  # MM/DD/YYYY — QBO US/CA standard

QBO_HEADERS = [
    "Journal No",
    "Journal Date",
    "Memo",
    "Account",
    "Debit",
    "Credit",
    "Description",
    "Name",
    "Class",
]


@dataclass
class QBOJournalLine:
    """A single line in a QBO Journal Entry."""
    journal_no: int
    journal_date: date
    memo: str
    account: str                # Account NAME (not code) in QBO
    debit: Decimal = ZERO
    credit: Decimal = ZERO
    description: str = ""
    name: str = ""              # Customer/vendor
    class_name: str = ""        # QBO Class (equivalent to Xero Tracking)


@dataclass
class QBOJournal:
    """A complete QBO Journal Entry."""
    journal_no: int
    lines: list[QBOJournalLine] = field(default_factory=list)

    def total_debits(self) -> Decimal:
        return sum(line.debit for line in self.lines)

    def total_credits(self) -> Decimal:
        return sum(line.credit for line in self.lines)

    def is_balanced(self) -> bool:
        return self.total_debits() == self.total_credits()


def format_qbo_date(d: date) -> str:
    """Format a date as MM/DD/YYYY for QBO."""
    return d.strftime(QBO_DATE_FORMAT)


def build_prepaid_amortization_journal_qbo(
    journal_no: int,
    period_date: date,
    amortization_amount: Decimal,
    description: str,
    expense_account_name: str,
    asset_account_name: str,
    class_name: str = "",
) -> QBOJournal:
    """
    Build a QBO journal for one month's prepaid amortization.
    DR Expense / CR Prepaid Asset.
    """
    memo = f"Prepaid Amortization - {period_date.strftime('%b %Y')}"
    amt = round_penny(amortization_amount)

    lines = [
        QBOJournalLine(
            journal_no=journal_no,
            journal_date=period_date,
            memo=memo,
            account=expense_account_name,
            debit=amt,
            credit=ZERO,
            description=description,
            class_name=class_name,
        ),
        QBOJournalLine(
            journal_no=journal_no,
            journal_date=period_date,
            memo=memo,
            account=asset_account_name,
            debit=ZERO,
            credit=amt,
            description=description,
            class_name=class_name,
        ),
    ]

    return QBOJournal(journal_no=journal_no, lines=lines)


def build_prepaid_setup_journal_qbo(
    journal_no: int,
    setup_date: date,
    prepaid_amount: Decimal,
    gst_hst_itc: Decimal,
    description: str,
    asset_account_name: str,
    cash_account_name: str,
    gst_receivable_account_name: str,
    class_name: str = "",
) -> QBOJournal:
    """
    Build a QBO journal for the initial prepaid setup.
    DR Prepaid Asset (+ DR GST/HST Receivable if ITC) / CR Cash.
    """
    memo = f"Prepaid Setup - {description}"
    lines = []

    # DR Prepaid Asset
    lines.append(QBOJournalLine(
        journal_no=journal_no,
        journal_date=setup_date,
        memo=memo,
        account=asset_account_name,
        debit=round_penny(prepaid_amount),
        credit=ZERO,
        description=f"{description} - prepaid asset",
        class_name=class_name,
    ))

    # DR GST/HST Receivable (if ITC > 0)
    if gst_hst_itc > ZERO:
        lines.append(QBOJournalLine(
            journal_no=journal_no,
            journal_date=setup_date,
            memo=memo,
            account=gst_receivable_account_name,
            debit=round_penny(gst_hst_itc),
            credit=ZERO,
            description=f"{description} - GST/HST ITC",
            class_name=class_name,
        ))

    # CR Cash
    total_cash = round_penny(prepaid_amount + gst_hst_itc)
    lines.append(QBOJournalLine(
        journal_no=journal_no,
        journal_date=setup_date,
        memo=memo,
        account=cash_account_name,
        debit=ZERO,
        credit=total_cash,
        description=f"{description} - payment",
        class_name=class_name,
    ))

    return QBOJournal(journal_no=journal_no, lines=lines)


def journals_to_csv_qbo(journals: list[QBOJournal]) -> str:
    """
    Convert a list of QBOJournals to a CSV string.
    UTF-8 without BOM.
    """
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    writer.writerow(QBO_HEADERS)

    for journal in journals:
        for line in journal.lines:
            debit_str = str(round_penny(line.debit)) if line.debit > ZERO else ""
            credit_str = str(round_penny(line.credit)) if line.credit > ZERO else ""

            writer.writerow([
                line.journal_no,
                format_qbo_date(line.journal_date),
                line.memo,
                line.account,
                debit_str,
                credit_str,
                line.description,
                line.name,
                line.class_name,
            ])

    return output.getvalue()
