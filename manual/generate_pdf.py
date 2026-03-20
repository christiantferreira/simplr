"""
Generate professional PDF user manual for Simplr.
Uses fpdf2 (LGPL — commercial use OK).
"""

from fpdf import FPDF
import os

SCREENSHOTS = os.path.join(os.path.dirname(__file__), "screenshots")
OUTPUT = os.path.join(os.path.dirname(__file__), "Simplr_User_Manual.pdf")

# Brand colors
PURPLE_DARK = (30, 16, 82)       # #1E1052
PURPLE_ACCENT = (124, 106, 237)  # #7C6AED
PURPLE_LIGHT = (240, 237, 251)   # #F0EDFB
WHITE = (255, 255, 255)
TEXT_PRIMARY = (26, 26, 46)      # #1A1A2E
TEXT_SECONDARY = (107, 114, 128) # #6B7280
BORDER_COLOR = (224, 224, 224)
SUCCESS_GREEN = (73, 196, 114)
WARNING_ORANGE = (245, 166, 35)
DANGER_RED = (233, 75, 60)


class SimplrManual(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*PURPLE_DARK)
        self.rect(0, 0, 210, 12, "F")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*WHITE)
        self.set_y(3)
        self.cell(0, 6, "Simplr User Manual  |  Phase 0 - Prepaid Expenses", align="C")
        self.set_text_color(*TEXT_PRIMARY)
        self.ln(14)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*TEXT_SECONDARY)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def cover_page(self):
        self.add_page()
        self.set_fill_color(*PURPLE_DARK)
        self.rect(0, 0, 210, 297, "F")

        self.set_font("Helvetica", "", 60)
        self.set_text_color(*PURPLE_ACCENT)
        self.set_y(70)
        self.cell(0, 20, "*", align="C")

        self.set_font("Helvetica", "B", 42)
        self.set_text_color(*WHITE)
        self.set_y(100)
        self.cell(0, 18, "Simplr", align="C")

        self.set_font("Helvetica", "", 16)
        self.set_text_color(*PURPLE_ACCENT)
        self.set_y(122)
        self.cell(0, 10, "Accounting schedules, simplified.", align="C")

        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*WHITE)
        self.set_y(160)
        self.cell(0, 12, "User Manual", align="C")

        self.set_font("Helvetica", "", 14)
        self.set_text_color(165, 148, 249)
        self.set_y(178)
        self.cell(0, 10, "Phase 0 - Prepaid Expenses Module", align="C")

        self.set_font("Helvetica", "", 11)
        self.set_text_color(*TEXT_SECONDARY)
        self.set_y(240)
        self.cell(0, 8, "Step-by-step guide for setup, data entry,", align="C")
        self.set_y(248)
        self.cell(0, 8, "report generation, and CSV export to Xero / QBO", align="C")

        self.set_font("Helvetica", "", 9)
        self.set_text_color(107, 114, 128)
        self.set_y(272)
        self.cell(0, 6, "Version 0.1.0  |  March 2026", align="C")

    def toc_page(self):
        self.add_page()
        self.section_title("Table of Contents")
        self.ln(4)

        toc_items = [
            ("1.", "Opening the App", ""),
            ("2.", "Understanding the Navigation", ""),
            ("3.", "Step 1: Client Setup", ""),
            ("", "3.1  Client Name and Fiscal Year", ""),
            ("", "3.2  Tax Configuration", ""),
            ("", "3.3  Chart of Accounts", ""),
            ("", "3.4  Xero Tax Rate Mapping", ""),
            ("", "3.5  Tracking Categories", ""),
            ("", "3.6  Special Accounts", ""),
            ("4.", "Step 2: Creating a Prepaid Contract", ""),
            ("5.", "Step 3: Viewing the Amortization Schedule", ""),
            ("6.", "Step 4: Generating the Roll-Forward Report", ""),
            ("7.", "Step 5: Exporting Journal Entries (CSV)", ""),
            ("8.", "Saving and Loading Your Work", ""),
            ("9.", "Example: Complete Walkthrough", ""),
            ("10.", "Troubleshooting & FAQ", ""),
        ]

        for num, title, _ in toc_items:
            if num:
                self.set_font("Helvetica", "B", 11)
                self.set_text_color(*PURPLE_ACCENT)
                self.cell(12, 8, num)
                self.set_font("Helvetica", "B", 11)
            else:
                self.cell(12, 8, "")
                self.set_font("Helvetica", "", 10)

            self.set_text_color(*TEXT_PRIMARY)
            self.cell(140, 8, title)
            self.ln()

    def section_title(self, title):
        self.ln(4)
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*PURPLE_DARK)
        self.cell(0, 12, title)
        self.ln(2)
        self.set_draw_color(*PURPLE_ACCENT)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def subsection_title(self, title):
        if self.get_y() > 250:
            self.add_page()
        self.ln(3)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*PURPLE_ACCENT)
        self.cell(0, 9, title)
        self.ln(7)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*TEXT_PRIMARY)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bold_text(self, text):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*TEXT_PRIMARY)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def important_box(self, text, color="purple"):
        if color == "purple":
            bg = PURPLE_LIGHT
            border = PURPLE_ACCENT
        elif color == "green":
            bg = (232, 250, 237)
            border = SUCCESS_GREEN
        elif color == "orange":
            bg = (255, 243, 224)
            border = WARNING_ORANGE
        elif color == "red":
            bg = (253, 232, 230)
            border = DANGER_RED
        else:
            bg = PURPLE_LIGHT
            border = PURPLE_ACCENT

        x = self.get_x()
        y = self.get_y()

        self.set_fill_color(*border)
        self.rect(x, y, 2, 18, "F")
        self.set_fill_color(*bg)
        self.rect(x + 2, y, 188, 18, "F")

        self.set_xy(x + 6, y + 2)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*border)
        self.multi_cell(182, 5, text)
        self.set_y(y + 20)

    def wide_important_box(self, text, color="purple"):
        if color == "purple":
            bg = PURPLE_LIGHT
            border = PURPLE_ACCENT
        elif color == "green":
            bg = (232, 250, 237)
            border = SUCCESS_GREEN
        elif color == "orange":
            bg = (255, 243, 224)
            border = WARNING_ORANGE
        elif color == "red":
            bg = (253, 232, 230)
            border = DANGER_RED
        else:
            bg = PURPLE_LIGHT
            border = PURPLE_ACCENT

        self.set_font("Helvetica", "B", 9)
        lines = text.split("\n")
        h = max(len(lines) * 6 + 6, 20)

        if self.get_y() + h > 270:
            self.add_page()

        x = self.get_x()
        y = self.get_y()

        self.set_fill_color(*border)
        self.rect(x, y, 2, h, "F")
        self.set_fill_color(*bg)
        self.rect(x + 2, y, 188, h, "F")

        self.set_xy(x + 6, y + 3)
        self.set_text_color(*border)
        self.multi_cell(182, 5.5, text)
        self.set_y(y + h + 3)

    def add_table(self, headers, rows, col_widths=None):
        if col_widths is None:
            w = 190 / len(headers)
            col_widths = [w] * len(headers)

        # Check space
        needed = (len(rows) + 1) * 8 + 10
        if self.get_y() + needed > 270:
            self.add_page()

        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(*PURPLE_DARK)
        self.set_text_color(*WHITE)
        self.set_draw_color(*BORDER_COLOR)

        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, h, border=1, fill=True, align="C")
        self.ln()

        self.set_font("Helvetica", "", 9)
        self.set_text_color(*TEXT_PRIMARY)
        alt = False
        for row in rows:
            if alt:
                self.set_fill_color(*PURPLE_LIGHT)
            else:
                self.set_fill_color(*WHITE)
            alt = not alt

            max_h = 8
            for i, cell_text in enumerate(row):
                lines = self.multi_cell(col_widths[i], 5, str(cell_text), dry_run=True, output="LINES")
                needed = len(lines) * 5 + 2
                if needed > max_h:
                    max_h = needed

            x_start = self.get_x()
            y_start = self.get_y()

            for i, cell_text in enumerate(row):
                x = x_start + sum(col_widths[:i])
                self.set_xy(x, y_start)
                if alt:
                    self.set_fill_color(*PURPLE_LIGHT)
                else:
                    self.set_fill_color(*WHITE)
                self.rect(x, y_start, col_widths[i], max_h, "FD")
                self.set_xy(x + 1, y_start + 1)
                self.multi_cell(col_widths[i] - 2, 5, str(cell_text))

            self.set_y(y_start + max_h)

        self.ln(3)

    def add_screenshot(self, filename, caption="", width=170):
        filepath = os.path.join(SCREENSHOTS, filename)
        if not os.path.exists(filepath):
            self.body_text(f"[Screenshot: {filename} - not found]")
            return

        if self.get_y() > 180:
            self.add_page()

        x = (210 - width) / 2
        self.set_draw_color(*BORDER_COLOR)
        self.set_line_width(0.3)
        self.image(filepath, x=x, w=width)
        self.ln(2)

        if caption:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(*TEXT_SECONDARY)
            self.cell(0, 5, caption, align="C")
            self.ln(5)

    def bullet(self, text, indent=10):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*TEXT_PRIMARY)
        x = self.get_x()
        self.set_x(x + indent)
        self.cell(5, 5.5, "-")
        self.multi_cell(170 - indent, 5.5, text)
        self.ln(1)

    def numbered_step(self, number, text):
        if self.get_y() > 265:
            self.add_page()
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*PURPLE_ACCENT)
        self.cell(8, 6, str(number) + ".")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*TEXT_PRIMARY)
        self.multi_cell(175, 6, text)
        self.ln(1)

    def code_block(self, text):
        self.set_font("Courier", "", 8)
        self.set_fill_color(245, 245, 250)
        self.set_draw_color(*BORDER_COLOR)
        self.set_text_color(60, 60, 80)

        lines = text.strip().split("\n")
        h = len(lines) * 4.5 + 6
        y = self.get_y()

        if y + h > 275:
            self.add_page()
            y = self.get_y()

        self.rect(10, y, 190, h, "FD")
        self.set_xy(13, y + 3)
        for line in lines:
            self.cell(0, 4.5, line)
            self.ln(4.5)
            self.set_x(13)
        self.set_y(y + h + 3)


def build_manual():
    pdf = SimplrManual()

    # ─── Cover ─────────────────────────────────────────
    pdf.cover_page()

    # ─── Table of Contents ─────────────────────────────
    pdf.toc_page()

    # ═══════════════════════════════════════════════════
    # Section 1: Opening the App
    # ═══════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("1. Opening the App")
    pdf.body_text(
        "Open your web browser and go to the Simplr URL provided to you. "
        "This can be either the Streamlit Cloud link (e.g., simplr-xxx.streamlit.app) "
        "or http://localhost:8501 if running locally on your computer."
    )
    pdf.body_text("You will see the Simplr app with:")
    pdf.bullet("A purple sidebar on the left with the Simplr logo and navigation")
    pdf.bullet("The main content area on the right showing the current page")
    pdf.ln(2)
    pdf.add_screenshot("01_setup_page.png", "Figure 1.1 - The Setup page is the first thing you see when opening Simplr")

    # ═══════════════════════════════════════════════════
    # Section 2: Navigation
    # ═══════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("2. Understanding the Navigation")
    pdf.body_text(
        "The sidebar on the left is your main navigation. Click on any page name to switch to it. "
        "The currently selected page shows a filled circle next to it."
    )
    pdf.add_screenshot("14_sidebar.png", "Figure 2.1 - The sidebar with navigation links, Save/Load buttons, and branding", width=70)

    pdf.ln(2)
    pdf.add_table(
        ["Page", "What it does"],
        [
            ["Setup", "Configure client info, tax rates, chart of accounts, Xero mappings"],
            ["Prepaid Entry", "Create new prepaid contracts"],
            ["Schedule View", "View calculated amortization schedules"],
            ["Report", "Generate roll-forward working paper reports"],
            ["Export JE", "Validate and download CSV files for Xero or QBO"],
        ],
        col_widths=[40, 150],
    )

    pdf.bold_text("Save / Load (bottom of sidebar):")
    pdf.bullet("Save Session button - downloads a JSON file with all your data")
    pdf.bullet("Drag and drop / Browse files area - upload a previously saved JSON to restore your work")
    pdf.add_screenshot("14_sidebar_save_load.png", "Figure 2.2 - Save Session and Load Session at the bottom of the sidebar", width=70)

    # ═══════════════════════════════════════════════════
    # Section 3: Client Setup
    # ═══════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("3. Step 1: Client Setup")
    pdf.wide_important_box("IMPORTANT: This is the FIRST thing you must do before anything else.\nThe Setup page configures the client tax rates, chart of accounts, and Xero/QBO mappings.", "purple")
    pdf.ln(2)
    pdf.body_text('Click "Setup" in the sidebar to begin. Below is the full Setup page:')
    pdf.add_screenshot("01_setup_page.png", "Figure 3.1 - The Setup page overview with Client Name, Province, and Fiscal Year")

    # 3.1
    pdf.subsection_title("3.1 Client Name and Fiscal Year")
    pdf.add_table(
        ["Field", "What to enter", "Example"],
        [
            ["Client Name", "The name of the client", "ABC Company Ltd."],
            ["Fiscal Year-End Month", "Month their fiscal year ends", "December (most common)"],
            ["Province", "Client province (auto-fills tax rates)", "BC (GST 5% + PST 7%)"],
        ],
        col_widths=[45, 85, 60],
    )
    pdf.body_text(
        "How Province works: When you select a province, the GST/HST and PST rates below automatically "
        "update to that province's rates. For example: BC = GST 5% + PST 7%, Ontario = HST 13% (no separate PST), "
        "Alberta = GST 5% only (no PST)."
    )

    # 3.2
    pdf.subsection_title("3.2 Tax Configuration")
    pdf.body_text("Scroll down to the Tax Configuration section:")
    pdf.add_screenshot("21_setup_tax_section.png", "Figure 3.2 - Tax configuration: GST/HST rate, PST rate, and recoverability checkboxes")
    pdf.add_table(
        ["Field", "What it means", "Default (BC)"],
        [
            ["GST/HST Rate (%)", "The GST or HST percentage", "5"],
            ["GST/HST Recoverable (ITC)", "Can client claim GST/HST as ITC?", "Checked"],
            ["PST Rate (%)", "The PST percentage", "7"],
            ["PST Recoverable", "Is PST recoverable? (almost never)", "Unchecked"],
        ],
        col_widths=[55, 85, 50],
    )

    pdf.wide_important_box(
        "WHY THIS MATTERS:\n"
        "- GST/HST Recoverable (checked): GST becomes a separate ITC entry, NOT added to the prepaid asset\n"
        "- PST Not Recoverable (unchecked): PST gets CAPITALIZED into the prepaid amount\n\n"
        "Example: $12,000 insurance in BC:\n"
        "  GST 5% = $600 ITC (separate)  |  PST 7% = $840 (added to prepaid)\n"
        "  Capitalized = $12,840  |  Total cash = $13,440",
        "purple",
    )

    # 3.3
    pdf.subsection_title("3.3 Chart of Accounts")
    pdf.body_text(
        "This is where you enter the account codes and names that match your Xero or QBO chart of accounts. "
        "Format: One account per line, as CODE | NAME"
    )
    pdf.add_screenshot("22_setup_coa.png", "Figure 3.3 - Chart of Accounts text area: enter one account per line as CODE | NAME")
    pdf.code_block(
        "1000 | Cash\n"
        "1200 | GST/HST Receivable\n"
        "1400 | Prepaid Expenses\n"
        "6100 | Office Expense\n"
        "6200 | Insurance Expense\n"
        "6300 | Software Expense"
    )
    pdf.body_text(
        "To customize: Delete accounts you do not need, add new ones that match your Xero/QBO. "
        "Make sure the codes and names match EXACTLY what is in your accounting system."
    )

    # 3.4
    pdf.subsection_title("3.4 Xero Tax Rate Mapping")
    pdf.wide_important_box(
        "CRITICAL FOR XERO IMPORTS: The TaxRateName must match EXACTLY (case-sensitive!) what\n"
        "appears in your client Xero account. 'Tax Exempt' is NOT the same as 'Tax exempt'.\n"
        "If the case does not match, the Xero import will fail silently.",
        "red",
    )
    pdf.ln(2)
    pdf.add_screenshot("23_setup_xero_mapping.png", "Figure 3.4 - Xero Tax Rate Names: must match exactly what is in your Xero account")
    pdf.body_text("To find the correct names: Log into Xero > Settings > General Settings > Tax Rates. Copy the exact names.")
    pdf.body_text("Default values provided:")
    pdf.code_block("Tax Exempt\nGST on Expenses\nHST ON EXPENSES")

    # 3.5
    pdf.subsection_title("3.5 Tracking Categories (Optional)")
    pdf.body_text("If your client uses Tracking Categories in Xero (or Classes in QBO):")
    pdf.add_table(
        ["Field", "What to enter", "Example"],
        [
            ["Tracking Category Name", "Name of the tracking category", "Department"],
            ["Tracking Option", "The specific option/value", "Administration"],
        ],
        col_widths=[55, 75, 60],
    )
    pdf.body_text("Leave both blank if the client does not use tracking categories.")

    # 3.6
    pdf.subsection_title("3.6 Special Accounts")
    pdf.add_screenshot("24_setup_special_accounts.png", "Figure 3.5 - Special Accounts: Cash/AP and GST/HST Receivable dropdowns")
    pdf.add_table(
        ["Field", "What to select", "Purpose"],
        [
            ["Cash / AP Account", "Account for cash payments", "Used in Setup JE (initial recording)"],
            ["GST/HST Receivable", "Account for GST/HST ITC", "Used when GST/HST is recoverable"],
        ],
        col_widths=[50, 60, 80],
    )

    # ═══════════════════════════════════════════════════
    # Section 4: Prepaid Entry
    # ═══════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("4. Step 2: Creating a Prepaid Contract")
    pdf.body_text('Click "Prepaid Entry" in the sidebar. You will see the empty contract entry form:')
    pdf.add_screenshot("02_prepaid_entry.png", "Figure 4.1 - The Prepaid Entry form (empty, ready to fill)")

    pdf.subsection_title("4.1 Fill in the Contract Details")
    pdf.bold_text("Left column fields:")
    pdf.add_table(
        ["Field", "What to enter", "Example"],
        [
            ["Description", "Clear name for this contract", "Insurance - Annual Policy 2026"],
            ["Total Amount (pre-tax)", "Contract amount BEFORE taxes", "12000.00"],
            ["Start Date", "When the prepaid period begins", "2026/01/01"],
            ["End Date", "When the prepaid period ends", "2026/12/31"],
        ],
        col_widths=[55, 70, 65],
    )

    pdf.bold_text("Right column fields:")
    pdf.add_table(
        ["Field", "What to select", "Example"],
        [
            ["Expense Account", "Expense account to debit monthly", "6200 - Insurance Expense"],
            ["Prepaid Asset Account", "Balance sheet account to credit", "1400 - Prepaid Expenses"],
            ["Xero TaxRateName", "Tax rate name for Xero export", "Tax Exempt"],
            ["Mid-Month Convention", "Check if contract starts mid-month", "Usually unchecked"],
            ["FX Rate", "Exchange rate (1.0 = CAD)", "1.0"],
        ],
        col_widths=[50, 75, 65],
    )

    pdf.body_text("Here is an example with the form filled in for ABC Company insurance policy:")
    pdf.add_screenshot("30_prepaid_entry_filling.png", "Figure 4.2 - Contract form filled with sample data: Insurance $12,000")

    pdf.wide_important_box(
        "MID-MONTH CONVENTION:\n"
        "- Unchecked (default): Equal monthly amounts. $12,000 / 12 = $1,000/month\n"
        "- Checked: First and last months get proportional share based on actual days.\n"
        "  Use this when the contract starts/ends mid-month and you need exact allocation.",
        "purple",
    )

    pdf.subsection_title("4.2 Tax Override (Optional)")
    pdf.body_text(
        "If this specific contract has different tax treatment than the client defaults, you can override here. "
        "Leave the override fields blank to use the client default rates from the Setup page."
    )
    pdf.add_screenshot("32_prepaid_entry_accounts.png", "Figure 4.3 - Tax Override section: leave blank to use client defaults")

    pdf.subsection_title("4.3 Calculate and Confirm")
    pdf.body_text(
        'Click the purple "Calculate Schedule" button at the bottom. '
        "If successful, you will see a green confirmation message."
    )
    pdf.add_screenshot("34_prepaid_calculated_success.png", "Figure 4.4 - Success! Contract calculated and added. Green message at bottom confirms it.")
    pdf.bullet("You can add multiple contracts by filling in the form again and clicking Calculate")
    pdf.bullet('To remove a contract, click the "Remove" button next to it in the list below the form')

    # ═══════════════════════════════════════════════════
    # Section 5: Schedule View
    # ═══════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("5. Step 3: Viewing the Amortization Schedule")
    pdf.body_text('Click "Schedule View" in the sidebar.')
    pdf.body_text(
        "This page shows the full amortization schedule for each contract, with summary metrics "
        "at the top and a detailed month-by-month breakdown."
    )
    pdf.add_screenshot("40_schedule_view.png", "Figure 5.1 - Schedule View showing the Insurance contract with all 12 months")

    pdf.subsection_title("5.1 Summary Metrics")
    pdf.body_text("At the top of each contract schedule, you see four key metrics:")
    pdf.add_table(
        ["Metric", "What it shows", "Example Value"],
        [
            ["Capitalized Amount", "Amount on the balance sheet (after PST if applicable)", "$12,840.00"],
            ["GST/HST ITC", "Separate ITC amount (if GST is recoverable)", "$600.00"],
            ["Total Cash Outflow", "Total paid (capitalized + ITC)", "$13,440.00"],
            ["Periods", "Number of months in the schedule", "12"],
        ],
        col_widths=[45, 100, 45],
    )

    pdf.subsection_title("5.2 Amortization Table")
    pdf.body_text("The table below the metrics shows the month-by-month amortization breakdown:")
    pdf.add_table(
        ["Column", "What it shows"],
        [
            ["Period", "The month (e.g., Jan 2026, Feb 2026, etc.)"],
            ["Opening Balance", "Balance at start of that month"],
            ["Amortization", "Amount expensed that month"],
            ["Ending Balance", "Balance after amortization"],
            ["Plug", "Yes on the last month (absorbs rounding difference)"],
        ],
        col_widths=[45, 145],
    )

    pdf.wide_important_box(
        "KEY THINGS TO VERIFY:\n"
        "- First month Opening Balance = the Capitalized Amount ($12,840.00)\n"
        "- Last month Ending Balance = $0.00 (always, exactly)\n"
        "- Sum of all Amortization amounts = Capitalized Amount (exactly)",
        "green",
    )

    # ═══════════════════════════════════════════════════
    # Section 6: Report
    # ═══════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("6. Step 4: Generating the Roll-Forward Report")
    pdf.body_text(
        'Click "Report" in the sidebar. This generates a working paper roll-forward report '
        "in the format CPAs expect: Opening Balance + Additions - Amortization = Ending Balance."
    )

    pdf.subsection_title("6.1 Set the Period")
    pdf.body_text("Choose the report period using the date fields at the top:")
    pdf.add_table(
        ["Field", "What to enter", "Example"],
        [
            ["Period Start", "First day of the report period", "2026/01/01"],
            ["Period End", "Last day of the report period", "2026/12/31"],
        ],
        col_widths=[45, 80, 65],
    )

    pdf.subsection_title("6.2 Generate the Report")
    pdf.body_text('Click the purple "Generate Report" button. Here is the result:')
    pdf.add_screenshot("51_report_generated.png", "Figure 6.1 - Roll-Forward Report for Jan-Dec 2026 showing full-year amortization")

    pdf.subsection_title("6.3 Report Columns Explained")
    pdf.add_table(
        ["Column", "Meaning"],
        [
            ["Contract", "Contract description"],
            ["Account", "Expense account code"],
            ["Opening", "Balance at start of period"],
            ["Additions", "New contracts added during period"],
            ["Amortization", "Total amortized during period"],
            ["Ending", "Balance at end of period"],
            ["Next JE", "Next month amortization amount (or Complete)"],
        ],
        col_widths=[40, 150],
    )

    pdf.body_text(
        "The system automatically verifies that Opening + Additions - Amortization = Ending. "
        "A green checkmark confirms the equation balances."
    )

    pdf.subsection_title("6.4 Export to XLSX")
    pdf.body_text(
        'Click the purple "Export to XLSX" button to download an Excel file with report metadata, '
        "per-contract breakdown, totals row, and professional formatting."
    )

    # ═══════════════════════════════════════════════════
    # Section 7: Export JE
    # ═══════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("7. Step 5: Exporting Journal Entries (CSV)")
    pdf.body_text(
        'Click "Export JE" in the sidebar. This is the final step - generating the CSV file '
        "to import into Xero or QBO."
    )

    pdf.subsection_title("7.1 Select Export Parameters")
    pdf.body_text("At the top of the page, configure the export:")
    pdf.add_screenshot("60_export_je.png", "Figure 7.1 - Export JE page: select Year, Month, Format (Xero/QBO)")
    pdf.add_table(
        ["Field", "What to select", "Notes"],
        [
            ["Year", "Year of the journal entries", "e.g., 2026"],
            ["Month", "Specific month to export", "January, February, etc."],
            ["Export Format", "Target system", "Xero or QBO"],
            ["Include Setup JEs", "Include initial recording?", "Only for the contract start month"],
        ],
        col_widths=[45, 65, 80],
    )

    pdf.subsection_title("7.2 Validate & Preview")
    pdf.body_text('Click the purple "Validate & Preview" button. The system checks:')
    pdf.bullet("Are all journal entries balanced (debits = credits)?")
    pdf.bullet("Do all account codes exist in your Chart of Accounts?")
    pdf.bullet("Does the TaxRateName match your configured mappings? (case-sensitive!)")
    pdf.bullet("Is the period open?")
    pdf.bullet("Was this period already exported? (warning if yes)")
    pdf.ln(1)
    pdf.body_text("Here is the result after successful validation:")
    pdf.add_screenshot("61_export_validated.png", "Figure 7.2 - Validation PASSED with CSV Preview showing the Xero journal entry")

    pdf.wide_important_box(
        "VALIDATION PASSED = green message. You can download the CSV.\n"
        "VALIDATION FAILED = red error messages. Fix issues in Setup, then try again.",
        "green",
    )

    pdf.subsection_title("7.3 Understanding the CSV Preview")
    pdf.body_text("The CSV content is shown in a preview box. Review carefully before downloading.")
    pdf.bold_text("For Xero CSV, verify:")
    pdf.bullet("Date format is DD MMM YYYY (e.g., 31 Jan 2026) - NEVER MM/DD/YYYY")
    pdf.bullet("Amounts: positive = debit, negative = credit")
    pdf.bullet("TaxRateName matches exactly what is in your Xero")
    pdf.ln(1)
    pdf.bold_text("For QBO CSV, verify:")
    pdf.bullet("Date format is MM/DD/YYYY (e.g., 01/31/2026)")
    pdf.bullet("Debit and Credit are in separate columns")
    pdf.bullet("Account names (not codes) match your QBO")

    pdf.subsection_title("7.4 Download and Import into Xero")
    pdf.numbered_step(1, 'Click "Download Xero CSV" (or "Download QBO CSV")')
    pdf.numbered_step(2, 'Click "Mark as Exported" to record this period was exported')
    pdf.numbered_step(3, "Open Xero > Accounting > Manual Journals > Import")
    pdf.numbered_step(4, "Upload the CSV file")
    pdf.numbered_step(5, "Xero shows a preview - verify it looks correct")
    pdf.numbered_step(6, "Click Import (journals arrive as Draft - review and post)")

    # ═══════════════════════════════════════════════════
    # Section 8: Save/Load
    # ═══════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("8. Saving and Loading Your Work")

    pdf.wide_important_box(
        "IMPORTANT: Simplr Phase 0 does not have a database. If you close the browser,\n"
        "your data is lost. ALWAYS use Save/Load to preserve your work.",
        "red",
    )
    pdf.ln(3)

    pdf.add_screenshot("14_sidebar_save_load.png", "Figure 8.1 - Save and Load controls in the sidebar", width=70)

    pdf.subsection_title("Saving Your Session")
    pdf.numbered_step(1, "Look at the sidebar (left side)")
    pdf.numbered_step(2, 'Click the "Save Session" button')
    pdf.numbered_step(3, "A JSON file downloads (e.g., simplr_session_2026-03-20.json)")
    pdf.numbered_step(4, "Keep this file safe - it contains all your client config and contracts")

    pdf.subsection_title("Loading a Previous Session")
    pdf.numbered_step(1, "Look at the sidebar (left side)")
    pdf.numbered_step(2, 'In the "Drag and drop file here" area:')
    pdf.bullet("Drag your saved JSON file onto it, OR")
    pdf.bullet('Click "Browse files" and select the JSON file')
    pdf.numbered_step(3, "The system loads all your data and you can continue where you left off")
    pdf.ln(2)

    pdf.wide_important_box(
        "TIP: Save your session after every significant change. Rename files meaningfully\n"
        "(e.g., simplr_ABC_Company_March2026.json) to stay organized.",
        "purple",
    )

    # ═══════════════════════════════════════════════════
    # Section 9: Complete Walkthrough with screenshots
    # ═══════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("9. Example: Complete Walkthrough")
    pdf.body_text(
        "This section walks through a real example from start to finish: "
        "ABC Company Ltd. in BC, with a $12,000 annual insurance policy."
    )

    pdf.subsection_title("Step 1: Setup")
    pdf.numbered_step(1, 'Click "Setup" in sidebar')
    pdf.numbered_step(2, "Enter Client Name: ABC Company Ltd.")
    pdf.numbered_step(3, "Select Province: BC (GST 5% + PST 7%)")
    pdf.numbered_step(4, "Fiscal Year-End Month: December")
    pdf.numbered_step(5, "Tax config auto-fills: GST 5% recoverable, PST 7% non-recoverable")
    pdf.numbered_step(6, "Verify Chart of Accounts matches your Xero")
    pdf.add_screenshot("01_setup_page.png", "Figure 9.1 - Setup page with ABC Company Ltd. configured", width=160)

    pdf.subsection_title("Step 2: Create Contract")
    pdf.numbered_step(1, 'Click "Prepaid Entry" in sidebar')
    pdf.numbered_step(2, "Description: Insurance - Annual Policy 2026")
    pdf.numbered_step(3, "Total Amount: 12000.00")
    pdf.numbered_step(4, "Start Date: 2026/01/01  |  End Date: 2026/12/31")
    pdf.numbered_step(5, "Expense Account: 6200 - Insurance Expense")
    pdf.numbered_step(6, "Prepaid Asset Account: 1400 - Prepaid Expenses")
    pdf.numbered_step(7, "Xero TaxRateName: Tax Exempt")
    pdf.numbered_step(8, 'Click "Calculate Schedule"')
    pdf.add_screenshot("34_prepaid_calculated_success.png", "Figure 9.2 - Contract calculated successfully (green message at bottom)")

    pdf.subsection_title("Step 3: Verify Schedule")
    pdf.body_text('Click "Schedule View". You should see:')
    pdf.add_screenshot("40_schedule_view.png", "Figure 9.3 - Amortization schedule with $1,070/month for 12 months")
    pdf.add_table(
        ["Metric", "Expected Value", "Why"],
        [
            ["Capitalized Amount", "$12,840.00", "$12,000 + 7% PST ($840)"],
            ["GST/HST ITC", "$600.00", "5% GST on $12,000"],
            ["Total Cash Outflow", "$13,440.00", "$12,840 + $600"],
            ["Monthly Amortization", "$1,070.00", "$12,840 / 12 months"],
            ["Periods", "12", "Jan to Dec 2026"],
            ["Final Ending Balance", "$0.00", "Always zero"],
        ],
        col_widths=[50, 45, 95],
    )

    pdf.subsection_title("Step 4: Generate Report")
    pdf.numbered_step(1, 'Click "Report" in sidebar')
    pdf.numbered_step(2, "Period Start: 2026/01/01  |  Period End: 2026/12/31")
    pdf.numbered_step(3, 'Click "Generate Report"')
    pdf.add_screenshot("51_report_generated.png", "Figure 9.4 - Roll-Forward Report: $12,840 Additions, $12,840 Amortization, $0 Ending")

    pdf.subsection_title("Step 5: Export January to Xero")
    pdf.numbered_step(1, 'Click "Export JE" | Year: 2026 | Month: January | Format: Xero')
    pdf.numbered_step(2, 'Click "Validate & Preview"')
    pdf.numbered_step(3, "Review the CSV preview")
    pdf.add_screenshot("61_export_validated.png", "Figure 9.5 - Validation PASSED: CSV ready to download for Xero import")
    pdf.numbered_step(4, 'Click "Download Xero CSV"')
    pdf.numbered_step(5, 'Click "Mark as Exported"')
    pdf.numbered_step(6, "Import into Xero > Accounting > Manual Journals > Import")

    pdf.subsection_title("Step 6: Export February")
    pdf.numbered_step(1, "Change Month to February")
    pdf.numbered_step(2, "Validate, Preview, Download, Import")
    pdf.body_text("Repeat for each subsequent month (March, April, etc.).")

    pdf.subsection_title("Step 7: Save Your Work")
    pdf.body_text('Click "Save Session" in the sidebar. Keep the file safe.')

    # ═══════════════════════════════════════════════════
    # Section 10: Troubleshooting
    # ═══════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("10. Troubleshooting & FAQ")

    issues = [
        (
            "Validation FAILED - INVALID_TAX_RATE",
            "The TaxRateName does not match what is in Xero. Go to Setup > Xero Tax Rate Mapping "
            "and make sure the names are EXACTLY the same (case-sensitive). Check your Xero account: "
            "Settings > Tax Rates.",
        ),
        (
            "Validation FAILED - INVALID_ACCOUNT",
            "An account code in the journal entry does not exist in your Chart of Accounts. "
            "Go to Setup > Chart of Accounts and add the missing account.",
        ),
        (
            "No journal entries found for this period",
            "The selected month does not have any entries. Check that you have created a contract "
            "and that the selected month falls within the contract start/end dates.",
        ),
        (
            "This period was previously exported",
            "This is a WARNING, not an error. It means you already exported this month. "
            "If you import again into Xero, you will create DUPLICATE entries.",
        ),
        (
            "Data disappeared after refreshing",
            "Simplr Phase 0 stores data in the browser session only. Always use Save Session "
            "to keep your work. Use Load Session (drag JSON file) to restore it.",
        ),
        (
            "How do I add more contracts?",
            "Go to Prepaid Entry and fill in the form again. Each Calculate Schedule click "
            "adds a new contract. All contracts appear together in Schedule View and Reports.",
        ),
        (
            "Can I edit a contract?",
            "In Phase 0, you cannot edit directly. Remove the contract (click Remove button) "
            "and re-create it with the correct values.",
        ),
        (
            "What is the Plug column?",
            "The last month absorbs any rounding difference (the plug). This ensures the ending "
            "balance is always exactly $0.00, even when amounts do not divide evenly.",
        ),
        (
            "The amounts do not look right",
            "Check: (1) Did you enter the PRE-TAX amount? (2) Is the province set correctly? "
            "(3) Is PST set to non-recoverable? BC PST gets added to the prepaid amount.",
        ),
    ]

    for question, answer in issues:
        if pdf.get_y() > 245:
            pdf.add_page()
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*PURPLE_DARK)
        pdf.set_x(10)
        pdf.multi_cell(190, 6, question)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*TEXT_PRIMARY)
        pdf.set_x(10)
        pdf.multi_cell(190, 5.5, answer)
        pdf.ln(4)

    # ─── Back cover ────────────────────────────────────
    pdf.add_page()
    pdf.set_fill_color(*PURPLE_DARK)
    pdf.rect(0, 0, 210, 297, "F")

    pdf.set_font("Helvetica", "", 40)
    pdf.set_text_color(*PURPLE_ACCENT)
    pdf.set_y(100)
    pdf.cell(0, 20, "*", align="C")

    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*WHITE)
    pdf.set_y(125)
    pdf.cell(0, 14, "Simplr", align="C")

    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(*PURPLE_ACCENT)
    pdf.set_y(143)
    pdf.cell(0, 8, "Accounting schedules, simplified.", align="C")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(165, 148, 249)
    pdf.set_y(175)
    pdf.cell(0, 6, "Need help? Contact your system administrator.", align="C")
    pdf.set_y(183)
    pdf.cell(0, 6, "Phase 0  |  Prepaid Expenses Module  |  Version 0.1.0", align="C")

    # Save
    pdf.output(OUTPUT)
    print(f"PDF saved to: {OUTPUT}")
    return OUTPUT


if __name__ == "__main__":
    build_manual()
