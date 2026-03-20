# Export Engine — Directives

## Xero Manual Journal CSV

### Format Spec
- **Encoding:** UTF-8 WITHOUT BOM
- **Line ending:** LF (`\n`)
- **Decimal separator:** Always period (`.`), never comma
- **Date format:** `DD MMM YYYY` (e.g., `31 Mar 2026`). NEVER `MM/DD/YYYY`.

### Required Headers (with asterisk prefix)
```
*Narration,*Date,*Description,*AccountCode,*TaxRateName,*Amount,Reference,TrackingName1,TrackingOption1
```

### Amount Convention
- **Positive = Debit**
- **Negative = Credit**
- Sum of `*Amount` per journal (same Narration + Date) MUST equal exactly `$0.00`

### TaxRateName
- **CASE-SENSITIVE.** `"Tax Exempt"` ≠ `"Tax exempt"` ≠ `"TAX EXEMPT"`
- Must match the exact string configured in the client's Xero account
- Common values: `"Tax Exempt"`, `"GST on Expenses"`, `"HST ON EXPENSES"`

### Reference
- Format: `SIMPLR-{MODULE}-{YYYY}-{MM}` (e.g., `SIMPLR-PP-2026-03`)
- Setup JEs use: `SIMPLR-PP-SETUP-{YYYY}-{MM}`

### Tracking Categories
- If the client uses tracking categories in Xero, `TrackingName1` and `TrackingOption1` are effectively required
- Without them, the bookkeeper must manually edit each imported JE

## QBO Journal Entry CSV

### Format Spec
- **Encoding:** UTF-8
- **Date format:** `MM/DD/YYYY` (e.g., `03/20/2026`)
- **NOT IIF format** (legacy, unstable)

### Headers
```
Journal No,Journal Date,Memo,Account,Debit,Credit,Description,Name,Class
```

### Key Differences from Xero
- Uses **account NAMES**, not codes
- Separate **Debit** and **Credit** columns (not single Amount)
- `Journal No` groups lines of the same JE (integer)
- `Class` = equivalent of Xero's Tracking Category

## Pre-Export Validation Checks
1. Each journal balanced (debits = credits exactly)
2. Account codes/names exist in configured COA
3. TaxRateName matches configured mapping (case-sensitive)
4. Date within open period
5. Warning if period already exported
6. Tracking/Class present if required by client config

## Export Tracking
- Each export generates unique Export ID + SHA-256 hash
- Export history stored in session (Phase 0) / database (Phase 1+)
- Re-export warning prevents accidental duplicates
