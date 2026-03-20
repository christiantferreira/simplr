# Calculation Engine — Directives

## Core Rules

1. **NEVER use `float` for monetary values.** All amounts MUST use Python `Decimal`.
2. **Banker's rounding (ROUND_HALF_EVEN)** applied per line when rounding to cents.
3. **Internal precision: 28 digits** (Python Decimal default). Rounding only at output.
4. **Plug/stub:** Last period in any schedule absorbs rounding difference to ensure total amortization == capitalized amount exactly.

## Prepaid Amortization

- **Method:** Linear, monthly periods.
- **Mid-month convention (optional):** When enabled, first and last months get partial fractions based on actual days / total days in month.
- **Without mid-month:** Equal allocation across all months. Last month absorbs remainder.

## Tax Treatment

- **PST non-recoverable:** Added to capitalized amount. The prepaid asset includes PST.
  - Example: $12,000 + 7% PST = $12,840 capitalized
- **GST/HST recoverable:** Separate ITC (Input Tax Credit). NOT added to capitalized amount.
  - Example: $12,000 + 5% GST = $12,000 capitalized + $600 ITC
- **Both:** PST added to asset, GST stays separate.
  - Example: $12,000 + 7% PST + 5% GST = $12,840 capitalized + $600 ITC

## FX Rate

- Static rate at inception (not dynamic).
- Applied to pre-tax amount: `base_amount_cad = total_amount * fx_rate`.
- Tax calculated on CAD amount.

## Period Generation

- Periods are calendar months (1st to last day).
- First period may start mid-month; last period may end mid-month.
- JE posting date = last day of the calendar month (month-end convention).

## Edge Cases Learned

- Single-period prepaid: entire amount amortized in one period.
- Amount not evenly divisible: plug ensures zero ending balance.
- Start date == End date: one period, full amortization.
