"""
Roll-Forward Working Paper Report Generator for Prepaid Expenses.

Format: Opening Balance + Additions - Amortization = Ending Balance
"""

from datetime import date
from decimal import Decimal
from dataclasses import dataclass

from ..calc.decimal_utils import ZERO, round_penny
from ..calc.prepaid import PrepaidResult


@dataclass
class RollForwardLine:
    """One contract's line in the roll-forward report."""
    description: str
    account: str
    opening_balance: Decimal
    additions: Decimal
    amortization: Decimal
    ending_balance: Decimal
    next_je_amount: Decimal
    next_je_month: str


@dataclass
class RollForwardReport:
    """Complete roll-forward report for a period."""
    client_name: str
    period_start: date
    period_end: date
    fiscal_year_end: str
    lines: list[RollForwardLine]
    total_opening: Decimal
    total_additions: Decimal
    total_amortization: Decimal
    total_ending: Decimal


def generate_roll_forward(
    results: list[PrepaidResult],
    period_start: date,
    period_end: date,
    client_name: str = "",
    fiscal_year_end: str = "December 31",
) -> RollForwardReport:
    """
    Generate a roll-forward report for a list of prepaid contracts
    over a specified period.

    The report shows:
    - Opening balance at period_start
    - Additions during period (new contracts starting in this period)
    - Amortization during period
    - Ending balance at period_end
    - Next JE amount and month
    """
    lines = []

    for result in results:
        schedule = result.schedule
        inp = result.input

        if not schedule:
            continue

        # Find opening balance (balance at start of period)
        opening = ZERO
        additions = ZERO
        amortization = ZERO

        # If contract starts before or at period_start, opening balance = balance
        # at the end of the month just before period_start
        contract_started_before_period = inp.start_date < period_start

        if contract_started_before_period:
            # Opening balance = balance at start of first period in range
            for line in schedule:
                if line.period_date >= period_start:
                    opening = line.opening_balance
                    break
            else:
                # Contract fully amortized before period
                opening = ZERO
        else:
            # Contract starts during or after this period — it's an addition
            if inp.start_date <= period_end:
                additions = result.capitalized_amount
                opening = ZERO
            else:
                # Contract starts after this period
                continue

        # Sum amortization within period
        for line in schedule:
            if period_start <= line.period_date <= period_end:
                amortization = round_penny(amortization + line.amortization)

        ending = round_penny(opening + additions - amortization)

        # Find next JE after period_end
        next_je_amount = ZERO
        next_je_month = ""
        for line in schedule:
            if line.period_date > period_end:
                next_je_amount = line.amortization
                next_je_month = line.period_date.strftime("%b %Y")
                break

        lines.append(RollForwardLine(
            description=inp.description,
            account=inp.expense_account_code,
            opening_balance=opening,
            additions=additions,
            amortization=amortization,
            ending_balance=ending,
            next_je_amount=next_je_amount,
            next_je_month=next_je_month,
        ))

    total_opening = round_penny(sum(l.opening_balance for l in lines))
    total_additions = round_penny(sum(l.additions for l in lines))
    total_amortization = round_penny(sum(l.amortization for l in lines))
    total_ending = round_penny(sum(l.ending_balance for l in lines))

    return RollForwardReport(
        client_name=client_name,
        period_start=period_start,
        period_end=period_end,
        fiscal_year_end=fiscal_year_end,
        lines=lines,
        total_opening=total_opening,
        total_additions=total_additions,
        total_amortization=total_amortization,
        total_ending=total_ending,
    )


def report_to_dict(report: RollForwardReport) -> dict:
    """Convert report to dict format for XLSX export."""
    contracts = []
    for line in report.lines:
        contracts.append({
            "description": line.description,
            "account": line.account,
            "opening_balance": line.opening_balance,
            "additions": line.additions,
            "amortization": line.amortization,
            "ending_balance": line.ending_balance,
            "next_je_amount": line.next_je_amount,
            "next_je_month": line.next_je_month,
        })

    return {
        "contracts": contracts,
        "totals": {
            "opening_balance": report.total_opening,
            "additions": report.total_additions,
            "amortization": report.total_amortization,
            "ending_balance": report.total_ending,
        },
    }
