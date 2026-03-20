# Testing — Directives

## Test Philosophy
- Tests written FIRST, then implementation.
- All monetary assertions use exact `Decimal` comparison (never float).
- Every schedule must end with balance == $0.00 exactly.

## Test Cases Covered

### Prepaid Calculation (test_prepaid_calc.py)
| Test | Input | Expected |
|------|-------|----------|
| Simple 12-month | $12,000 / 12 months | $1,000/month, ending = $0 |
| Mid-month | $12,000, Mar 15 to Mar 14 | 13 periods, partial first/last |
| PST non-recoverable (BC) | $12,000 + 7% PST | $12,840 capitalized |
| GST recoverable | $12,000 + 5% GST | $12,000 cap + $600 ITC |
| GST + PST (BC) | $12,000 + 5% GST + 7% PST | $12,840 cap + $600 ITC |
| FX rate | $10,000 USD * 1.35 | $13,500 CAD capitalized |
| Odd amount | $10,000 / 12 | Plug ensures ending = $0 |
| Short period | $3,000 / 3 months | $1,000/month |

### Xero Export (test_xero_export.py)
| Test | Validates |
|------|-----------|
| Date format | DD MMM YYYY, never MM/DD/YYYY |
| Amount signs | Positive = debit, negative = credit |
| CSV encoding | UTF-8 without BOM |
| Decimal separator | Always period |
| TaxRateName | Exact case-sensitive string preserved |
| Tracking | TrackingName1/TrackingOption1 included |
| Balance | Sum of amounts per journal = $0.00 |
| Headers | Asterisk prefix on required fields |
| Setup JE with ITC | 3 lines, balanced |

### QBO Export (test_qbo_export.py)
| Test | Validates |
|------|-----------|
| Date format | MM/DD/YYYY |
| Debit/Credit columns | Separate columns, correct values |
| Account names | Uses names not codes |
| Class | Included when provided |
| Journal numbering | Distinct per JE |
| Balance | Debits = Credits |

### Roll-Forward (test_roll_forward.py)
| Test | Validates |
|------|-----------|
| Q1 report | Opening + Additions - Amort = Ending |
| Mid-year | Correct opening from prior periods |
| Next JE | Shows next month's amount |
| Fully amortized | Zero balances after contract ends |
| Multiple contracts | Totals add up correctly |

### Pre-Export Validation (test_validators.py)
| Test | Validates |
|------|-----------|
| Missing account code | Error raised |
| Wrong TaxRateName case | Error raised (case-sensitive) |
| Unbalanced journal | Error raised |
| Closed period | Error raised |
| Already exported | Warning raised |
| Missing tracking | Error if required |

## Running Tests
```bash
cd simplr
python -m pytest tests/ -v
```
