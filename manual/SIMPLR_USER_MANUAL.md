# Simplr — User Manual (Phase 0)

## Prepaid Expenses Module — Step-by-Step Guide

---

## Table of Contents

1. [Opening the App](#1-opening-the-app)
2. [Understanding the Navigation](#2-understanding-the-navigation)
3. [Step 1: Client Setup](#3-step-1-client-setup)
4. [Step 2: Creating a Prepaid Contract](#4-step-2-creating-a-prepaid-contract)
5. [Step 3: Viewing the Amortization Schedule](#5-step-3-viewing-the-amortization-schedule)
6. [Step 4: Generating the Roll-Forward Report](#6-step-4-generating-the-roll-forward-report)
7. [Step 5: Exporting Journal Entries (CSV)](#7-step-5-exporting-journal-entries-csv)
8. [Saving and Loading Your Work](#8-saving-and-loading-your-work)
9. [Example: Complete Walkthrough](#9-example-complete-walkthrough)
10. [Troubleshooting & FAQ](#10-troubleshooting--faq)

---

## 1. Opening the App

Open your web browser and go to the Simplr URL provided to you (either the Streamlit Cloud link or `http://localhost:8501` if running locally).

You will see the Simplr app with:
- A **purple sidebar** on the left with the Simplr logo (✦) and navigation
- The **main content area** on the right

![Simplr Setup Page](screenshots/01_setup_page.png)

---

## 2. Understanding the Navigation

The sidebar on the left contains everything you need:

![Sidebar Navigation](screenshots/14_sidebar.png)

### Navigation Pages (top of sidebar):
| Page | What it does |
|------|-------------|
| **Setup** | Configure client info, tax rates, chart of accounts, Xero mappings |
| **Prepaid Entry** | Create new prepaid contracts |
| **Schedule View** | View calculated amortization schedules |
| **Report** | Generate roll-forward working paper reports |
| **Export JE** | Validate and download CSV files for Xero or QBO |

### Save / Load (bottom of sidebar):
- **Save Session** button — downloads a JSON file with all your data
- **Drag and drop / Browse files** area — upload a previously saved JSON file to restore your work

**IMPORTANT:** Click each page name to navigate. The currently selected page shows a filled circle (●) next to it.

---

## 3. Step 1: Client Setup

**This is the FIRST thing you must do before anything else.** The Setup page configures the client's tax rates, chart of accounts, and Xero/QBO mappings.

Click **"Setup"** in the sidebar.

![Setup Page](screenshots/01_setup_page.png)

### 3.1 Client Name and Fiscal Year

| Field | What to enter | Example |
|-------|--------------|---------|
| **Client Name** | The name of the client you're working on | `ABC Company Ltd.` |
| **Fiscal Year-End Month** | The month their fiscal year ends | `December` (most common) |
| **Province** | The client's province — this auto-fills tax rates | `BC (GST 5% + PST 7%)` |

**How Province works:** When you select a province, the GST/HST and PST rates below automatically update to that province's rates. For example:
- BC → GST 5% + PST 7%
- Ontario → HST 13% (no separate PST)
- Alberta → GST 5% only (no PST)

### 3.2 Tax Configuration

| Field | What it means | Default for BC |
|-------|--------------|----------------|
| **GST/HST Rate (%)** | The GST or HST percentage | `5` |
| **GST/HST Recoverable (ITC)** | Check this if the client can claim GST/HST as Input Tax Credit | ✅ Checked |
| **PST Rate (%)** | The PST percentage | `7` |
| **PST Recoverable** | Check this if PST is recoverable (almost never in Canada) | ☐ Unchecked |

**Why this matters:**
- If GST/HST is **recoverable** (checked) → the GST amount becomes a separate ITC entry, NOT added to the prepaid asset
- If PST is **not recoverable** (unchecked) → the PST gets **capitalized into the prepaid amount** (added to the asset value)

**Example:** A $12,000 insurance policy in BC:
- GST 5% recoverable → $600 ITC (separate)
- PST 7% not recoverable → $840 added to prepaid
- Capitalized prepaid amount = $12,000 + $840 = **$12,840**
- Total cash outflow = $12,840 + $600 = **$13,440**

### 3.3 Chart of Accounts

This is where you enter the account codes and names that match your Xero or QBO chart of accounts.

**Format:** One account per line, in the format: `CODE | NAME`

**Default accounts provided:**
```
1000 | Cash
1200 | GST/HST Receivable
1400 | Prepaid Expenses
6100 | Office Expense
6200 | Insurance Expense
6300 | Software Expense
```

**To customize:**
1. Delete any accounts you don't need
2. Add new accounts that match your Xero/QBO setup
3. Make sure the codes and names match **exactly** what's in Xero/QBO

**Example:** If your client's Xero has account code `5200` for "Insurance Expense", change `6200 | Insurance Expense` to `5200 | Insurance Expense`.

### 3.4 Xero Tax Rate Mapping

**This is CRITICAL for Xero imports.** The TaxRateName must match **exactly** (case-sensitive!) what appears in your client's Xero account.

**Default values:**
```
Tax Exempt
GST on Expenses
HST ON EXPENSES
```

**To find the correct names:**
1. Log into Xero → Settings → General Settings → Tax Rates
2. Copy the exact names (including capitalization) into this field
3. One name per line

**WARNING:** `"Tax Exempt"` is NOT the same as `"Tax exempt"` or `"TAX EXEMPT"`. If the case doesn't match exactly, the Xero import will fail.

### 3.5 Tracking Categories (Optional)

If your client uses Tracking Categories in Xero (or Classes in QBO):

| Field | What to enter | Example |
|-------|--------------|---------|
| **Tracking Category Name** | The name of the tracking category in Xero | `Department` |
| **Tracking Option** | The specific option/value | `Administration` |

Leave both blank if the client doesn't use tracking categories.

### 3.6 Special Accounts

| Field | What to select | Purpose |
|-------|---------------|---------|
| **Cash / AP Account** | The account used for cash payments | Used in the Setup JE (initial recording) |
| **GST/HST Receivable Account** | The account for GST/HST ITC | Used when GST/HST is recoverable |

---

## 4. Step 2: Creating a Prepaid Contract

Click **"Prepaid Entry"** in the sidebar.

![Prepaid Entry Page](screenshots/02_prepaid_entry.png)

### 4.1 Fill in the Contract Details

**Left column:**

| Field | What to enter | Example |
|-------|--------------|---------|
| **Description** | A clear name for this prepaid contract | `Insurance - Annual Policy 2026` |
| **Total Amount (pre-tax)** | The contract amount BEFORE any taxes | `12000` |
| **Start Date** | When the prepaid period begins | `2026/01/01` |
| **End Date** | When the prepaid period ends | `2026/12/31` |

**Right column:**

| Field | What to select | Example |
|-------|---------------|---------|
| **Expense Account** | The expense account to debit each month | `6200 - Insurance Expense` |
| **Prepaid Asset Account** | The balance sheet account to credit each month | `1400 - Prepaid Expenses` |
| **Xero TaxRateName** | The tax rate name for Xero export | `Tax Exempt` |
| **Mid-Month Convention** | Check if the contract starts/ends mid-month | Usually ☐ unchecked |
| **FX Rate at Inception** | Exchange rate if contract is in foreign currency | `1.0` for CAD |

**About Mid-Month Convention:**
- **Unchecked (default):** Each month gets an equal share of the total. If $12,000 over 12 months = $1,000/month.
- **Checked:** The first and last months get a proportional share based on actual days. Use this if the contract starts or ends in the middle of a month and you want exact day-based allocation.

### 4.2 Tax Override (Optional)

If this specific contract has different tax treatment than the client defaults, you can override here:

| Field | When to use |
|-------|-------------|
| **GST/HST Rate Override** | If this contract has a different GST/HST rate |
| **PST Rate Override** | If this contract has a different PST rate |
| **GST/HST Recoverable** | Uncheck if this specific contract's GST is not recoverable |
| **PST Recoverable** | Check if this specific contract's PST is recoverable |

**If you leave the override fields blank**, the system uses the client default rates from the Setup page.

### 4.3 Calculate

Click the purple **"Calculate Schedule"** button at the bottom.

If successful, you'll see a green message: `Contract 'Insurance - Annual Policy 2026' added. 1 total contracts.`

The contract now appears in the "Existing Contracts" section below the form. You can add more contracts by filling in the form again.

**To remove a contract:** Click the "Remove" button next to it.

---

## 5. Step 3: Viewing the Amortization Schedule

Click **"Schedule View"** in the sidebar.

This page shows the calculated amortization schedule for each contract.

### What you'll see:

**Summary metrics at the top:**
- **Capitalized Amount** — the amount on the balance sheet (after PST if applicable)
- **GST/HST ITC** — the separate ITC amount (if GST is recoverable)
- **Total Cash Outflow** — total paid (capitalized + ITC)
- **Periods** — number of months in the schedule

**Amortization table:**
| Column | What it shows |
|--------|-------------|
| **Period** | The month (e.g., "Jan 2026") |
| **Opening Balance** | Balance at start of that month |
| **Amortization** | Amount expensed that month |
| **Ending Balance** | Balance after amortization |
| **Plug** | Shows "Yes" on the last month (absorbs rounding) |

**Key things to verify:**
- The first month's Opening Balance = the Capitalized Amount
- The last month's Ending Balance = **$0.00** (always)
- The sum of all Amortization amounts = the Capitalized Amount (exactly)

---

## 6. Step 4: Generating the Roll-Forward Report

Click **"Report"** in the sidebar.

This generates a **working paper roll-forward report** — the format CPAs expect.

### 6.1 Set the Period

| Field | What to enter | Example |
|-------|--------------|---------|
| **Period Start** | First day of the report period | `2026/01/01` |
| **Period End** | Last day of the report period | `2026/03/31` (Q1) |

### 6.2 Generate

Click the purple **"Generate Report"** button.

### 6.3 What you'll see:

**Report table showing:**
| Column | Meaning |
|--------|---------|
| **Contract** | Contract description |
| **Account** | Expense account code |
| **Opening** | Balance at start of period |
| **Additions** | New contracts added during period |
| **Amortization** | Total amortized during period |
| **Ending** | Balance at end of period |
| **Next JE** | Next month's amortization amount |

**Totals row** below the table shows aggregated amounts.

**Equation verification:** The system automatically checks that:
> Opening + Additions - Amortization = Ending

If the equation balances, you'll see a green checkmark. If not, you'll see a red error (this should never happen).

### 6.4 Export to XLSX

Click the purple **"Export to XLSX"** button to download an Excel file with:
- Report metadata (client name, fiscal year, dates)
- Per-contract breakdown
- Totals row
- Professional formatting (Simplr purple headers)

---

## 7. Step 5: Exporting Journal Entries (CSV)

Click **"Export JE"** in the sidebar.

This is the final step — generating the CSV file to import into Xero or QBO.

### 7.1 Select Export Parameters

| Field | What to select | Notes |
|-------|---------------|-------|
| **Year** | The year of the journal entries | `2026` |
| **Month** | The specific month to export | `January`, `February`, etc. |
| **Export Format** | Target system | `Xero` or `QBO` |
| **Include Setup JEs** | Check to include the initial prepaid recording | Only check for the month the contract starts |

### 7.2 Validate & Preview

Click the purple **"Validate & Preview"** button.

The system runs these validation checks:
- Are all journal entries balanced (debits = credits)?
- Do all account codes exist in your Chart of Accounts?
- Does the TaxRateName match your configured mappings? (case-sensitive!)
- Is the period open?
- Was this period already exported? (warning if yes)

**If validation passes:** You'll see a green "Validation PASSED" message.

**If validation fails:** You'll see red error messages explaining what's wrong. Fix the issues in the Setup page and try again.

### 7.3 Preview the CSV

The CSV content is shown in a preview box. **Review it carefully** before downloading.

**For Xero CSV, verify:**
- Date format is `DD MMM YYYY` (e.g., `31 Jan 2026`) — NEVER `MM/DD/YYYY`
- Amounts: positive = debit, negative = credit
- TaxRateName matches exactly what's in your Xero

**For QBO CSV, verify:**
- Date format is `MM/DD/YYYY` (e.g., `01/31/2026`)
- Debit and Credit are in separate columns
- Account names (not codes) match your QBO

### 7.4 Download

Click the purple **"Download Xero CSV"** (or **"Download QBO CSV"**) button to save the file.

### 7.5 Mark as Exported

After downloading, click **"Mark as Exported"** to record that this period has been exported. This prevents accidental duplicate exports.

### 7.6 Import into Xero

1. Open Xero → Accounting → Manual Journals
2. Click "Import" (or go to Settings → Import)
3. Upload the CSV file
4. Xero will show a preview — verify it looks correct
5. Click "Import" to create the journal entries
6. The journals will arrive as **Draft** — review and post them

---

## 8. Saving and Loading Your Work

**IMPORTANT:** Simplr Phase 0 does not have a database. If you close the browser, your data is lost. Use Save/Load to preserve your work.

### Saving

1. Look at the **sidebar** (left side)
2. Click the **"Save Session"** button
3. A JSON file will download (e.g., `simplr_session_2026-03-20.json`)
4. **Keep this file safe** — it contains all your client config and contracts

### Loading

1. Look at the **sidebar** (left side)
2. In the "Drag and drop file here" area, either:
   - Drag your saved JSON file onto it, OR
   - Click **"Browse files"** and select the JSON file
3. The system will load all your data and you can continue where you left off

**Tip:** Save your session after every significant change. Name files meaningfully (e.g., rename to `simplr_ABC_Company_March2026.json`).

---

## 9. Example: Complete Walkthrough

Let's walk through a real example: **ABC Company Ltd. in BC, with a $12,000 annual insurance policy.**

### Step 1: Setup

1. Click **"Setup"** in sidebar
2. Enter:
   - Client Name: `ABC Company Ltd.`
   - Province: `BC (GST 5% + PST 7%)`
   - Fiscal Year-End Month: `December`
3. Tax Configuration should auto-fill:
   - GST/HST Rate: `5`, GST/HST Recoverable: ✅
   - PST Rate: `7`, PST Recoverable: ☐
4. Chart of Accounts: keep defaults or customize to match Xero
5. Xero Tax Rate Mapping: verify names match your Xero account

### Step 2: Create Contract

1. Click **"Prepaid Entry"** in sidebar
2. Fill in:
   - Description: `Insurance - Annual Policy 2026`
   - Total Amount: `12000`
   - Start Date: `2026/01/01`
   - End Date: `2026/12/31`
   - Expense Account: `6200 - Insurance Expense`
   - Prepaid Asset Account: `1400 - Prepaid Expenses`
   - Xero TaxRateName: `Tax Exempt`
   - Mid-Month Convention: ☐ unchecked
   - FX Rate: `1.0`
3. Leave Tax Override blank (uses client defaults)
4. Click **"Calculate Schedule"**

### Step 3: Verify Schedule

1. Click **"Schedule View"** in sidebar
2. You should see:
   - Capitalized Amount: **$12,840.00** (12,000 + 7% PST)
   - GST/HST ITC: **$600.00**
   - Periods: **12**
   - Monthly amortization: **$1,070.00** ($12,840 / 12)
   - Last month ending balance: **$0.00**

### Step 4: Generate Report

1. Click **"Report"** in sidebar
2. Set Period Start: `2026/01/01`, Period End: `2026/03/31`
3. Click **"Generate Report"**
4. You should see:
   - Additions: $12,840 (new contract)
   - Amortization: $3,210 ($1,070 x 3 months)
   - Ending: $9,630
5. Click **"Export to XLSX"** to download the working paper

### Step 5: Export to Xero

1. Click **"Export JE"** in sidebar
2. Select Year: `2026`, Month: `January`, Format: `Xero`
3. Check **"Include Setup JEs"** (since January is when the contract starts)
4. Click **"Validate & Preview"**
5. Review the CSV preview:
   ```
   *Narration,*Date,*Description,*AccountCode,*TaxRateName,*Amount,Reference,...
   Prepaid Setup - Insurance...,01 Jan 2026,...,1400,Tax Exempt,12840.00,...
   Prepaid Setup - Insurance...,01 Jan 2026,...,1200,GST on Expenses,600.00,...
   Prepaid Setup - Insurance...,01 Jan 2026,...,1000,Tax Exempt,-13440.00,...
   Prepaid Amortization - Jan 2026,31 Jan 2026,...,6200,Tax Exempt,1070.00,...
   Prepaid Amortization - Jan 2026,31 Jan 2026,...,1400,Tax Exempt,-1070.00,...
   ```
6. Click **"Download Xero CSV"**
7. Click **"Mark as Exported"**

### Step 6: Export February (no setup JE needed)

1. Stay on **"Export JE"**
2. Change Month to `February`
3. **Uncheck** "Include Setup JEs" (already recorded in January)
4. Click **"Validate & Preview"**
5. Download and import into Xero

### Step 7: Save Your Work

1. Click **"Save Session"** in the sidebar
2. Keep the downloaded JSON file safe

---

## 10. Troubleshooting & FAQ

### "Validation FAILED — INVALID_TAX_RATE"
The TaxRateName doesn't match what's in Xero. Go to Setup → Xero Tax Rate Mapping and make sure the names are **exactly** the same (case-sensitive). Check your Xero account: Settings → Tax Rates.

### "Validation FAILED — INVALID_ACCOUNT"
An account code in the journal entry doesn't exist in your Chart of Accounts. Go to Setup → Chart of Accounts and add the missing account.

### "No journal entries found for this period"
The selected month doesn't have any amortization entries. Check that:
- You've created a contract in "Prepaid Entry"
- The month you selected falls within the contract's start/end dates

### "This period was previously exported"
This is a warning, not an error. It means you already exported this month before. If you import again into Xero, you'll create **duplicate** journal entries. Only re-export if you're sure the previous import failed.

### Data disappeared after refreshing the page
Simplr Phase 0 stores data in the browser session only. If you refresh the page or close the tab, data is reset. **Always use "Save Session" to keep your work.** Use "Load Session" to restore it.

### How do I add more contracts?
Go to "Prepaid Entry" and fill in the form again. Each time you click "Calculate Schedule", a new contract is added. All contracts appear in Schedule View and Reports together.

### Can I edit a contract after creating it?
In Phase 0, you cannot edit directly. Instead:
1. Remove the contract (click "Remove" button on the Prepaid Entry page)
2. Re-create it with the correct values

### What's the "Plug" column in the schedule?
The last month is marked as "Plug" because it absorbs any rounding difference. This ensures the ending balance is always **exactly $0.00**, even when the monthly amount doesn't divide evenly.

### The amounts don't look right
Check:
- Did you enter the **pre-tax** amount? (Total Amount field should not include taxes)
- Is the province set correctly? (affects PST capitalization)
- Is PST set to non-recoverable? (BC PST gets added to the prepaid amount)

---

*Simplr — Accounting schedules, simplified.*
*Phase 0 — Prepaid Expenses Module*
