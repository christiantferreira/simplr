"""
Simplr — Phase 0 Streamlit Prototype
Prepaid Expenses Module: Calculate, Report, Export
"""

import streamlit as st
import json
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from execution.calc.decimal_utils import ZERO, round_penny, to_decimal
from execution.calc.prepaid import PrepaidInput, TaxConfig, calculate_prepaid, PrepaidResult
from execution.calc.date_utils import last_day_of_month
from execution.export.xero_adapter import (
    build_prepaid_amortization_journal, build_prepaid_setup_journal,
    journals_to_csv, generate_reference, compute_export_hash, generate_export_id,
)
from execution.export.qbo_adapter import (
    build_prepaid_amortization_journal_qbo, build_prepaid_setup_journal_qbo,
    journals_to_csv_qbo,
)
from execution.export.xlsx_export import export_roll_forward_xlsx
from execution.reports.roll_forward import generate_roll_forward, report_to_dict
from execution.validators.pre_export import validate_xero_journals, validate_qbo_journals

# ─── Page Config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Simplr — Accounting Schedules",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Session State Init ───────────────────────────────────────────────────────

if "client_config" not in st.session_state:
    st.session_state.client_config = {
        "client_name": "",
        "fiscal_year_end_month": 12,
        "fiscal_year_end_day": 31,
        "province": "BC",
        "gst_hst_rate": "5",
        "gst_hst_recoverable": True,
        "pst_rate": "7",
        "pst_recoverable": False,
        "account_codes": ["1000", "1200", "1400", "6100", "6200", "6300"],
        "account_names": {
            "1000": "Cash",
            "1200": "GST/HST Receivable",
            "1400": "Prepaid Expenses",
            "6100": "Office Expense",
            "6200": "Insurance Expense",
            "6300": "Software Expense",
        },
        "xero_tax_rate_names": ["Tax Exempt", "GST on Expenses", "HST ON EXPENSES"],
        "tracking_name": "",
        "tracking_option": "",
        "cash_account_code": "1000",
        "gst_receivable_account_code": "1200",
        # QBO account names
        "qbo_account_names": [
            "Cash", "GST Receivable", "Prepaid Expenses",
            "Office Expense", "Insurance Expense", "Software Expense",
        ],
    }

if "contracts" not in st.session_state:
    st.session_state.contracts = []

if "results" not in st.session_state:
    st.session_state.results = []

if "exported_periods" not in st.session_state:
    st.session_state.exported_periods = []

# ─── Province Tax Defaults ─────────────────────────────────────────────────────

PROVINCE_TAX = {
    "BC": {"gst_hst_rate": "5", "pst_rate": "7", "label": "BC (GST 5% + PST 7%)"},
    "AB": {"gst_hst_rate": "5", "pst_rate": "0", "label": "AB (GST 5%)"},
    "SK": {"gst_hst_rate": "5", "pst_rate": "6", "label": "SK (GST 5% + PST 6%)"},
    "MB": {"gst_hst_rate": "5", "pst_rate": "7", "label": "MB (GST 5% + PST 7%)"},
    "ON": {"gst_hst_rate": "13", "pst_rate": "0", "label": "ON (HST 13%)"},
    "QC": {"gst_hst_rate": "5", "pst_rate": "9.975", "label": "QC (GST 5% + QST 9.975%)"},
    "NB": {"gst_hst_rate": "15", "pst_rate": "0", "label": "NB (HST 15%)"},
    "NS": {"gst_hst_rate": "15", "pst_rate": "0", "label": "NS (HST 15%)"},
    "PE": {"gst_hst_rate": "15", "pst_rate": "0", "label": "PE (HST 15%)"},
    "NL": {"gst_hst_rate": "15", "pst_rate": "0", "label": "NL (HST 15%)"},
    "NT": {"gst_hst_rate": "5", "pst_rate": "0", "label": "NT (GST 5%)"},
    "NU": {"gst_hst_rate": "5", "pst_rate": "0", "label": "NU (GST 5%)"},
    "YT": {"gst_hst_rate": "5", "pst_rate": "0", "label": "YT (GST 5%)"},
}

# ─── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 1rem 0;">
            <span style="font-size: 2rem; color: #7C6AED;">✦</span>
            <h1 style="color: #1E1052; margin: 0; font-size: 1.5rem;">Simplr</h1>
            <p style="color: #6B7280; font-size: 0.85rem; margin-top: 0.25rem;">Accounting schedules, simplified.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    page = st.radio(
        "Navigation",
        ["Setup", "Prepaid Entry", "Schedule View", "Report", "Export JE"],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("Phase 0 — Prepaid Expenses")
    st.caption("Works with Xero | Works with QBO")


# ─── Helper Functions ──────────────────────────────────────────────────────────

def safe_decimal(value: str, default: str = "0") -> Decimal:
    """Safely convert user input to Decimal."""
    try:
        return to_decimal(value.strip().replace(",", "")) if value.strip() else to_decimal(default)
    except (InvalidOperation, ValueError):
        return to_decimal(default)


def get_open_periods() -> list[str]:
    """Generate a list of open period strings for the current and next year."""
    today = date.today()
    periods = []
    for year in range(today.year - 1, today.year + 2):
        for month in range(1, 13):
            periods.append(f"{year:04d}-{month:02d}")
    return periods


def recalculate_all():
    """Recalculate all contract results."""
    cfg = st.session_state.client_config
    results = []
    for contract in st.session_state.contracts:
        try:
            tax_config = TaxConfig(
                gst_hst_rate=to_decimal(contract.get("gst_hst_rate", cfg["gst_hst_rate"])),
                gst_hst_recoverable=contract.get("gst_hst_recoverable", cfg["gst_hst_recoverable"]),
                pst_rate=to_decimal(contract.get("pst_rate", cfg["pst_rate"])),
                pst_recoverable=contract.get("pst_recoverable", cfg["pst_recoverable"]),
            )
            inp = PrepaidInput(
                description=contract["description"],
                total_amount=to_decimal(contract["total_amount"]),
                start_date=contract["start_date"],
                end_date=contract["end_date"],
                expense_account_code=contract["expense_account_code"],
                expense_account_name=cfg["account_names"].get(
                    contract["expense_account_code"], contract["expense_account_code"]
                ),
                asset_account_code=contract["asset_account_code"],
                asset_account_name=cfg["account_names"].get(
                    contract["asset_account_code"], contract["asset_account_code"]
                ),
                tax_config=tax_config,
                mid_month_convention=contract.get("mid_month_convention", False),
                fx_rate=to_decimal(contract.get("fx_rate", "1")),
                fiscal_year_end_month=cfg["fiscal_year_end_month"],
                fiscal_year_end_day=cfg["fiscal_year_end_day"],
                tracking_name=cfg.get("tracking_name", ""),
                tracking_option=cfg.get("tracking_option", ""),
                client_name=cfg["client_name"],
                xero_tax_rate_name=contract.get("xero_tax_rate_name", "Tax Exempt"),
            )
            result = calculate_prepaid(inp)
            results.append(result)
        except Exception as e:
            st.error(f"Error calculating {contract.get('description', 'unknown')}: {e}")
    st.session_state.results = results


# ─── Page: Setup ───────────────────────────────────────────────────────────────

if page == "Setup":
    st.header("Client Setup")
    st.caption("Configure client details, tax rates, chart of accounts, and export mappings.")

    cfg = st.session_state.client_config

    col1, col2 = st.columns(2)
    with col1:
        cfg["client_name"] = st.text_input("Client Name", value=cfg["client_name"])

        province = st.selectbox(
            "Province",
            options=list(PROVINCE_TAX.keys()),
            format_func=lambda p: PROVINCE_TAX[p]["label"],
            index=list(PROVINCE_TAX.keys()).index(cfg["province"]),
        )
        if province != cfg["province"]:
            cfg["province"] = province
            cfg["gst_hst_rate"] = PROVINCE_TAX[province]["gst_hst_rate"]
            cfg["pst_rate"] = PROVINCE_TAX[province]["pst_rate"]

    with col2:
        fy_month = st.selectbox(
            "Fiscal Year-End Month",
            options=list(range(1, 13)),
            format_func=lambda m: date(2026, m, 1).strftime("%B"),
            index=cfg["fiscal_year_end_month"] - 1,
        )
        cfg["fiscal_year_end_month"] = fy_month
        cfg["fiscal_year_end_day"] = last_day_of_month(2026, fy_month).day

    st.subheader("Tax Configuration")
    col1, col2 = st.columns(2)
    with col1:
        cfg["gst_hst_rate"] = st.text_input("GST/HST Rate (%)", value=cfg["gst_hst_rate"])
        cfg["gst_hst_recoverable"] = st.checkbox("GST/HST Recoverable (ITC)", value=cfg["gst_hst_recoverable"])
    with col2:
        cfg["pst_rate"] = st.text_input("PST Rate (%)", value=cfg["pst_rate"])
        cfg["pst_recoverable"] = st.checkbox("PST Recoverable", value=cfg["pst_recoverable"])

    st.subheader("Chart of Accounts")
    st.caption("Account codes used in journal entries. Add or remove as needed.")

    # Editable COA
    coa_text = st.text_area(
        "Account Codes and Names (one per line: CODE | NAME)",
        value="\n".join(f"{code} | {name}" for code, name in cfg["account_names"].items()),
        height=200,
    )
    # Parse COA
    new_codes = []
    new_names = {}
    for line in coa_text.strip().split("\n"):
        if "|" in line:
            parts = line.split("|", 1)
            code = parts[0].strip()
            name = parts[1].strip()
            if code:
                new_codes.append(code)
                new_names[code] = name
    cfg["account_codes"] = new_codes
    cfg["account_names"] = new_names
    cfg["qbo_account_names"] = list(new_names.values())

    st.subheader("Xero Tax Rate Mapping")
    st.caption("Exact TaxRateName strings from your Xero account (CASE-SENSITIVE).")
    tax_names_text = st.text_area(
        "Xero TaxRateNames (one per line)",
        value="\n".join(cfg["xero_tax_rate_names"]),
        height=100,
    )
    cfg["xero_tax_rate_names"] = [n.strip() for n in tax_names_text.strip().split("\n") if n.strip()]

    st.subheader("Tracking Categories (Optional)")
    col1, col2 = st.columns(2)
    with col1:
        cfg["tracking_name"] = st.text_input("Tracking Category Name", value=cfg.get("tracking_name", ""))
    with col2:
        cfg["tracking_option"] = st.text_input("Tracking Option", value=cfg.get("tracking_option", ""))

    st.subheader("Special Accounts")
    col1, col2 = st.columns(2)
    with col1:
        cfg["cash_account_code"] = st.selectbox(
            "Cash / AP Account (for Setup JE)",
            options=cfg["account_codes"],
            index=cfg["account_codes"].index(cfg["cash_account_code"]) if cfg["cash_account_code"] in cfg["account_codes"] else 0,
        )
    with col2:
        cfg["gst_receivable_account_code"] = st.selectbox(
            "GST/HST Receivable Account (for ITC)",
            options=cfg["account_codes"],
            index=cfg["account_codes"].index(cfg["gst_receivable_account_code"]) if cfg["gst_receivable_account_code"] in cfg["account_codes"] else 0,
        )

    st.success("Configuration saved to session.")


# ─── Page: Prepaid Entry ───────────────────────────────────────────────────────

elif page == "Prepaid Entry":
    st.header("New Prepaid Contract")
    st.caption("Enter contract details to generate an amortization schedule.")

    cfg = st.session_state.client_config

    with st.form("prepaid_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            description = st.text_input("Description", placeholder="e.g., Insurance - Annual Policy")
            total_amount = st.text_input("Total Amount (pre-tax)", placeholder="12000.00")
            start_date = st.date_input("Start Date", value=date.today())
            end_date = st.date_input("End Date", value=date.today() + timedelta(days=365))

        with col2:
            expense_codes = [c for c in cfg["account_codes"] if c.startswith("6") or c.startswith("5")]
            if not expense_codes:
                expense_codes = cfg["account_codes"]
            expense_account_code = st.selectbox("Expense Account", options=expense_codes,
                format_func=lambda c: f"{c} - {cfg['account_names'].get(c, c)}")

            asset_codes = [c for c in cfg["account_codes"] if c.startswith("1")]
            if not asset_codes:
                asset_codes = cfg["account_codes"]
            asset_account_code = st.selectbox("Prepaid Asset Account", options=asset_codes,
                format_func=lambda c: f"{c} - {cfg['account_names'].get(c, c)}")

            xero_tax_rate_name = st.selectbox("Xero TaxRateName", options=cfg["xero_tax_rate_names"])
            mid_month = st.checkbox("Mid-Month Convention")
            fx_rate = st.text_input("FX Rate at Inception (1.0 = CAD)", value="1.0")

        st.subheader("Tax Override (leave blank to use client defaults)")
        tc1, tc2 = st.columns(2)
        with tc1:
            override_gst = st.text_input("GST/HST Rate Override (%)", value="")
            override_gst_recov = st.checkbox("GST/HST Recoverable", value=cfg["gst_hst_recoverable"], key="entry_gst_recov")
        with tc2:
            override_pst = st.text_input("PST Rate Override (%)", value="")
            override_pst_recov = st.checkbox("PST Recoverable", value=cfg["pst_recoverable"], key="entry_pst_recov")

        submitted = st.form_submit_button("Calculate Schedule", type="primary", use_container_width=True)

        if submitted:
            if not description:
                st.error("Description is required.")
            elif not total_amount:
                st.error("Total amount is required.")
            elif start_date >= end_date:
                st.error("End date must be after start date.")
            else:
                contract = {
                    "description": description,
                    "total_amount": total_amount.strip().replace(",", ""),
                    "start_date": start_date,
                    "end_date": end_date,
                    "expense_account_code": expense_account_code,
                    "asset_account_code": asset_account_code,
                    "xero_tax_rate_name": xero_tax_rate_name,
                    "mid_month_convention": mid_month,
                    "fx_rate": fx_rate.strip() or "1.0",
                    "gst_hst_rate": override_gst.strip() or cfg["gst_hst_rate"],
                    "gst_hst_recoverable": override_gst_recov,
                    "pst_rate": override_pst.strip() or cfg["pst_rate"],
                    "pst_recoverable": override_pst_recov,
                }
                st.session_state.contracts.append(contract)
                recalculate_all()
                st.success(f"Contract '{description}' added. {len(st.session_state.contracts)} total contracts.")

    # Show existing contracts
    if st.session_state.contracts:
        st.subheader("Existing Contracts")
        for i, c in enumerate(st.session_state.contracts):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{c['description']}** — ${c['total_amount']} ({c['start_date']} to {c['end_date']})")
            with col2:
                st.write(f"Acct: {c['expense_account_code']}")
            with col3:
                if st.button("Remove", key=f"rm_{i}"):
                    st.session_state.contracts.pop(i)
                    recalculate_all()
                    st.rerun()


# ─── Page: Schedule View ───────────────────────────────────────────────────────

elif page == "Schedule View":
    st.header("Amortization Schedules")

    if not st.session_state.results:
        st.info("No contracts calculated yet. Go to 'Prepaid Entry' to add contracts.")
    else:
        for result in st.session_state.results:
            inp = result.input
            st.subheader(f"{inp.description}")

            # Summary
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Capitalized Amount", f"${result.capitalized_amount:,.2f}")
            col2.metric("GST/HST ITC", f"${result.gst_hst_itc_amount:,.2f}")
            col3.metric("Total Cash Outflow", f"${result.total_cash_outflow:,.2f}")
            col4.metric("Periods", len(result.schedule))

            # Schedule table
            table_data = []
            for line in result.schedule:
                table_data.append({
                    "Period": line.period_date.strftime("%b %Y"),
                    "Opening Balance": f"${line.opening_balance:,.2f}",
                    "Amortization": f"${line.amortization:,.2f}",
                    "Ending Balance": f"${line.ending_balance:,.2f}",
                    "Plug": "Yes" if line.is_plug else "",
                })

            st.dataframe(
                table_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Opening Balance": st.column_config.TextColumn(width="medium"),
                    "Amortization": st.column_config.TextColumn(width="medium"),
                    "Ending Balance": st.column_config.TextColumn(width="medium"),
                },
            )
            st.divider()


# ─── Page: Report ──────────────────────────────────────────────────────────────

elif page == "Report":
    st.header("Roll-Forward Report")
    st.caption("Working paper format: Opening Balance + Additions - Amortization = Ending Balance")

    if not st.session_state.results:
        st.info("No contracts calculated yet. Go to 'Prepaid Entry' to add contracts.")
    else:
        cfg = st.session_state.client_config

        col1, col2 = st.columns(2)
        with col1:
            report_start = st.date_input("Period Start", value=date(date.today().year, 1, 1))
        with col2:
            report_end = st.date_input("Period End", value=date(date.today().year, 12, 31))

        if st.button("Generate Report", type="primary"):
            report = generate_roll_forward(
                results=st.session_state.results,
                period_start=report_start,
                period_end=report_end,
                client_name=cfg["client_name"],
                fiscal_year_end=date(2026, cfg["fiscal_year_end_month"], cfg["fiscal_year_end_day"]).strftime("%B %d"),
            )

            # Display report
            st.subheader(f"Prepaid Expenses Roll-Forward: {report_start.strftime('%b %Y')} to {report_end.strftime('%b %Y')}")

            if report.lines:
                table_data = []
                for line in report.lines:
                    next_je = f"${line.next_je_amount:,.2f} - {line.next_je_month}" if line.next_je_amount > ZERO else "Complete"
                    table_data.append({
                        "Contract": line.description,
                        "Account": line.account,
                        "Opening": f"${line.opening_balance:,.2f}",
                        "Additions": f"${line.additions:,.2f}",
                        "Amortization": f"${line.amortization:,.2f}",
                        "Ending": f"${line.ending_balance:,.2f}",
                        "Next JE": next_je,
                    })

                st.dataframe(table_data, use_container_width=True, hide_index=True)

                # Totals
                st.markdown(
                    f"**TOTAL:** Opening ${report.total_opening:,.2f} + "
                    f"Additions ${report.total_additions:,.2f} - "
                    f"Amortization ${report.total_amortization:,.2f} = "
                    f"**Ending ${report.total_ending:,.2f}**"
                )

                # Verify equation
                computed = round_penny(report.total_opening + report.total_additions - report.total_amortization)
                if computed == report.total_ending:
                    st.success("Equation verified: Opening + Additions - Amortization = Ending")
                else:
                    st.error(f"EQUATION MISMATCH: computed {computed} != reported {report.total_ending}")

                # XLSX Export
                report_dict = report_to_dict(report)
                xlsx_bytes = export_roll_forward_xlsx(
                    report_data=report_dict,
                    client_name=cfg["client_name"],
                    fiscal_year_end=date(2026, cfg["fiscal_year_end_month"], cfg["fiscal_year_end_day"]).strftime("%B %d"),
                    report_date=date.today(),
                    period_start=report_start,
                    period_end=report_end,
                )

                st.download_button(
                    label="Export to XLSX",
                    data=xlsx_bytes,
                    file_name=f"Simplr_RollForward_{report_start.strftime('%Y%m')}_to_{report_end.strftime('%Y%m')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True,
                )
            else:
                st.warning("No contract data found for this period.")


# ─── Page: Export JE ───────────────────────────────────────────────────────────

elif page == "Export JE":
    st.header("Export Journal Entries")
    st.caption("Select a period, validate, preview, and download CSV for Xero or QBO.")

    if not st.session_state.results:
        st.info("No contracts calculated yet. Go to 'Prepaid Entry' to add contracts.")
    else:
        cfg = st.session_state.client_config

        col1, col2, col3 = st.columns(3)
        with col1:
            export_year = st.selectbox("Year", options=list(range(2024, 2030)), index=2)
        with col2:
            export_month = st.selectbox(
                "Month",
                options=list(range(1, 13)),
                format_func=lambda m: date(2026, m, 1).strftime("%B"),
            )
        with col3:
            export_format = st.selectbox("Export Format", ["Xero", "QBO"])

        include_setup = st.checkbox("Include Setup JEs (initial recording)", value=False)

        period_date = last_day_of_month(export_year, export_month)
        period_key = f"{export_year:04d}-{export_month:02d}"

        if period_key in st.session_state.exported_periods:
            st.warning(f"Period {period_key} was previously exported. Re-exporting may cause duplicates in your accounting system.")

        if st.button("Validate & Preview", type="primary"):
            if export_format == "Xero":
                _export_xero(period_date, period_key, include_setup, cfg)
            else:
                _export_qbo(period_date, period_key, include_setup, cfg)


def _export_xero(period_date, period_key, include_setup, cfg):
    """Handle Xero export flow."""
    journals = []

    for result in st.session_state.results:
        inp = result.input
        ref = generate_reference("PP", period_date.year, period_date.month)

        # Setup JE (if requested and period matches contract start)
        if include_setup and inp.start_date.month == period_date.month and inp.start_date.year == period_date.year:
            setup_j = build_prepaid_setup_journal(
                setup_date=inp.start_date,
                prepaid_amount=result.capitalized_amount,
                gst_hst_itc=result.gst_hst_itc_amount,
                description=inp.description,
                asset_account_code=inp.asset_account_code,
                cash_account_code=cfg["cash_account_code"],
                gst_receivable_account_code=cfg["gst_receivable_account_code"],
                tax_rate_name_asset=inp.xero_tax_rate_name,
                tax_rate_name_gst="GST on Expenses" if result.gst_hst_itc_amount > ZERO else inp.xero_tax_rate_name,
                reference=f"SIMPLR-PP-SETUP-{period_date.year:04d}-{period_date.month:02d}",
                tracking_name=inp.tracking_name,
                tracking_option=inp.tracking_option,
            )
            journals.append(setup_j)

        # Amortization JE for this period
        for line in result.schedule:
            if line.period_date == period_date:
                j = build_prepaid_amortization_journal(
                    period_date=period_date,
                    amortization_amount=line.amortization,
                    description=f"{inp.description} - monthly amort",
                    expense_account_code=inp.expense_account_code,
                    asset_account_code=inp.asset_account_code,
                    tax_rate_name=inp.xero_tax_rate_name,
                    reference=ref,
                    tracking_name=inp.tracking_name,
                    tracking_option=inp.tracking_option,
                )
                journals.append(j)

    if not journals:
        st.warning("No journal entries found for this period.")
        return

    # Validate
    validation = validate_xero_journals(
        journals=journals,
        configured_account_codes=cfg["account_codes"],
        configured_tax_rate_names=cfg["xero_tax_rate_names"],
        open_periods=get_open_periods(),
        exported_periods=st.session_state.exported_periods,
        require_tracking=bool(cfg.get("tracking_name")),
    )

    # Show validation results
    if validation.errors:
        st.error(f"Validation FAILED — {len(validation.errors)} error(s)")
        for issue in validation.errors:
            st.error(f"[{issue.code}] {issue.message}")
    else:
        st.success("Validation PASSED")

    if validation.warnings:
        for issue in validation.warnings:
            st.warning(f"[{issue.code}] {issue.message}")

    # Preview
    csv_content = journals_to_csv(journals)
    st.subheader("CSV Preview")
    st.code(csv_content, language="csv")

    # Summary
    total_debits = sum(
        line.amount for j in journals for line in j.lines if line.amount > ZERO
    )
    total_credits = sum(
        line.amount for j in journals for line in j.lines if line.amount < ZERO
    )
    st.write(f"**Total Debits:** ${total_debits:,.2f} | **Total Credits:** ${abs(total_credits):,.2f} | **Net:** ${total_debits + total_credits:,.2f}")

    # Download
    if validation.is_valid:
        export_hash = compute_export_hash(csv_content)
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download Xero CSV",
                data=csv_content.encode("utf-8"),
                file_name=f"Simplr_Xero_JE_{period_key}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )
        with col2:
            if st.button("Mark as Exported", use_container_width=True):
                st.session_state.exported_periods.append(period_key)
                st.success(f"Period {period_key} marked as exported. Hash: {export_hash[:12]}...")


def _export_qbo(period_date, period_key, include_setup, cfg):
    """Handle QBO export flow."""
    journals = []
    journal_no = 1

    for result in st.session_state.results:
        inp = result.input

        # Setup JE
        if include_setup and inp.start_date.month == period_date.month and inp.start_date.year == period_date.year:
            setup_j = build_prepaid_setup_journal_qbo(
                journal_no=journal_no,
                setup_date=inp.start_date,
                prepaid_amount=result.capitalized_amount,
                gst_hst_itc=result.gst_hst_itc_amount,
                description=inp.description,
                asset_account_name=cfg["account_names"].get(inp.asset_account_code, inp.asset_account_code),
                cash_account_name=cfg["account_names"].get(cfg["cash_account_code"], "Cash"),
                gst_receivable_account_name=cfg["account_names"].get(cfg["gst_receivable_account_code"], "GST Receivable"),
                class_name=inp.tracking_option,
            )
            journals.append(setup_j)
            journal_no += 1

        # Amortization JE
        for line in result.schedule:
            if line.period_date == period_date:
                j = build_prepaid_amortization_journal_qbo(
                    journal_no=journal_no,
                    period_date=period_date,
                    amortization_amount=line.amortization,
                    description=f"{inp.description} - monthly amort",
                    expense_account_name=cfg["account_names"].get(inp.expense_account_code, inp.expense_account_code),
                    asset_account_name=cfg["account_names"].get(inp.asset_account_code, inp.asset_account_code),
                    class_name=inp.tracking_option,
                )
                journals.append(j)
                journal_no += 1

    if not journals:
        st.warning("No journal entries found for this period.")
        return

    # Validate
    validation = validate_qbo_journals(
        journals=journals,
        configured_account_names=cfg["qbo_account_names"],
        open_periods=get_open_periods(),
        exported_periods=st.session_state.exported_periods,
        require_class=bool(cfg.get("tracking_name")),
    )

    if validation.errors:
        st.error(f"Validation FAILED — {len(validation.errors)} error(s)")
        for issue in validation.errors:
            st.error(f"[{issue.code}] {issue.message}")
    else:
        st.success("Validation PASSED")

    if validation.warnings:
        for issue in validation.warnings:
            st.warning(f"[{issue.code}] {issue.message}")

    csv_content = journals_to_csv_qbo(journals)
    st.subheader("CSV Preview")
    st.code(csv_content, language="csv")

    total_debits = sum(line.debit for j in journals for line in j.lines)
    total_credits = sum(line.credit for j in journals for line in j.lines)
    st.write(f"**Total Debits:** ${total_debits:,.2f} | **Total Credits:** ${total_credits:,.2f}")

    if validation.is_valid:
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download QBO CSV",
                data=csv_content.encode("utf-8"),
                file_name=f"Simplr_QBO_JE_{period_key}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )
        with col2:
            if st.button("Mark as Exported", use_container_width=True, key="qbo_mark"):
                st.session_state.exported_periods.append(period_key)
                st.success(f"Period {period_key} marked as exported.")
