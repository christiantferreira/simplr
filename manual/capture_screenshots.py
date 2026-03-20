"""
Capture detailed screenshots of Simplr app with fictitious data filled in.
Uses Playwright to navigate and interact with the Streamlit app.
"""

import time
import os
from playwright.sync_api import sync_playwright

SCREENSHOTS = os.path.join(os.path.dirname(__file__), "screenshots")
BASE_URL = "http://localhost:8501"


def wait_for_app(page, t=2):
    """Wait for Streamlit to finish loading."""
    time.sleep(t)
    try:
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=5000)
    except:
        pass
    time.sleep(0.5)


def click_nav(page, page_name):
    """Click a navigation item in the sidebar."""
    try:
        page.click(f'label:has-text("{page_name}")', timeout=3000)
    except:
        try:
            page.click(f'text="{page_name}"', timeout=2000)
        except:
            pass
    time.sleep(2)


def fill_by_aria(page, aria_label, value, clear=True):
    """Fill input by aria-label."""
    try:
        inp = page.locator(f'input[aria-label="{aria_label}"]').first
        if inp.is_visible():
            inp.click()
            if clear:
                inp.press("Control+a")
            inp.fill(value)
            inp.press("Tab")
            time.sleep(0.3)
            return True
    except Exception as e:
        print(f"    Could not fill '{aria_label}': {e}")
    return False


def take_screenshot(page, name, full_page=True):
    """Take a screenshot and save it."""
    filepath = os.path.join(SCREENSHOTS, name)
    page.screenshot(path=filepath, full_page=full_page)
    print(f"  Saved: {name}")


def main():
    os.makedirs(SCREENSHOTS, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2,
        )
        page = context.new_page()

        # ──────────────────────────────────────────────────
        # 1. SETUP PAGE
        # ──────────────────────────────────────────────────
        print("1. Setup page...")
        page.goto(BASE_URL)
        wait_for_app(page, 3)

        # Fill Client Name
        fill_by_aria(page, "Client Name", "ABC Company Ltd.")
        time.sleep(1)

        # Top of page - client name area
        take_screenshot(page, "01_setup_page.png")

        # Scroll to tax section
        page.evaluate("window.scrollBy(0, 400)")
        time.sleep(1)
        take_screenshot(page, "21_setup_tax_section.png")

        # Scroll to COA
        page.evaluate("window.scrollBy(0, 500)")
        time.sleep(1)
        take_screenshot(page, "22_setup_coa.png")

        # Scroll to Xero mapping
        page.evaluate("window.scrollBy(0, 500)")
        time.sleep(1)
        take_screenshot(page, "23_setup_xero_mapping.png")

        # Scroll to special accounts
        page.evaluate("window.scrollBy(0, 400)")
        time.sleep(1)
        take_screenshot(page, "24_setup_special_accounts.png")

        # Sidebar
        print("  Capturing sidebar...")
        try:
            sidebar = page.locator('[data-testid="stSidebar"]').first
            if sidebar.is_visible():
                sidebar.screenshot(path=os.path.join(SCREENSHOTS, "14_sidebar.png"))
                print("  Saved: 14_sidebar.png")
        except:
            pass

        # ──────────────────────────────────────────────────
        # 2. PREPAID ENTRY - EMPTY
        # ──────────────────────────────────────────────────
        print("\n2. Prepaid Entry page (empty)...")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)
        click_nav(page, "Prepaid Entry")
        wait_for_app(page)
        take_screenshot(page, "02_prepaid_entry.png")

        # ──────────────────────────────────────────────────
        # 3. FILL IN CONTRACT
        # ──────────────────────────────────────────────────
        print("\n3. Filling contract details...")

        # Description
        fill_by_aria(page, "Description", "Insurance - Annual Policy 2026")

        # Total Amount - it's a text input with placeholder 12000.00
        fill_by_aria(page, "Total Amount (pre-tax)", "12000.00")

        # Dates
        fill_by_aria(page, "Select a date.", "2026/01/01")

        time.sleep(0.5)
        take_screenshot(page, "30_prepaid_entry_filling.png")

        # Fill second date (end date)
        try:
            date_inputs = page.locator('input[aria-label="Select a date."]').all()
            print(f"  Found {len(date_inputs)} date inputs")
            if len(date_inputs) >= 2:
                date_inputs[1].click()
                date_inputs[1].press("Control+a")
                date_inputs[1].fill("2026/12/31")
                date_inputs[1].press("Tab")
                time.sleep(0.5)
        except Exception as e:
            print(f"  Date fill error: {e}")

        time.sleep(1)
        take_screenshot(page, "31_prepaid_entry_dates.png")

        # Scroll to see right column and more fields
        page.evaluate("window.scrollBy(0, 300)")
        time.sleep(1)
        take_screenshot(page, "32_prepaid_entry_accounts.png")

        # Scroll to Calculate button
        page.evaluate("window.scrollBy(0, 300)")
        time.sleep(1)
        take_screenshot(page, "33_prepaid_calc_button.png")

        # Click Calculate Schedule
        print("  Clicking Calculate Schedule...")
        try:
            calc_btn = page.locator('button:has-text("Calculate Schedule")').first
            if calc_btn.is_visible():
                calc_btn.click()
                time.sleep(3)
                # Scroll to top to see success message
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)
                take_screenshot(page, "34_prepaid_calculated_success.png")

                # Scroll to see existing contracts
                page.evaluate("window.scrollBy(0, 600)")
                time.sleep(1)
                take_screenshot(page, "35_prepaid_existing_contracts.png")
        except Exception as e:
            print(f"  Could not calculate: {e}")

        # ──────────────────────────────────────────────────
        # 4. SCHEDULE VIEW WITH DATA
        # ──────────────────────────────────────────────────
        print("\n4. Schedule View...")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)
        click_nav(page, "Schedule View")
        wait_for_app(page, 3)
        take_screenshot(page, "40_schedule_view.png")

        # Scroll to see summary metrics
        page.evaluate("window.scrollBy(0, 200)")
        time.sleep(1)
        take_screenshot(page, "41_schedule_metrics.png")

        # Scroll to see schedule table
        page.evaluate("window.scrollBy(0, 350)")
        time.sleep(1)
        take_screenshot(page, "42_schedule_table.png")

        # Scroll more to see remaining months
        page.evaluate("window.scrollBy(0, 350)")
        time.sleep(1)
        take_screenshot(page, "43_schedule_table2.png")

        # ──────────────────────────────────────────────────
        # 5. REPORT PAGE
        # ──────────────────────────────────────────────────
        print("\n5. Report page...")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)
        click_nav(page, "Report")
        wait_for_app(page, 3)
        take_screenshot(page, "50_report_page.png")

        # Click Generate Report
        print("  Clicking Generate Report...")
        try:
            gen_btn = page.locator('button:has-text("Generate Report")').first
            if not gen_btn.is_visible():
                gen_btn = page.locator('button:has-text("Generate")').first
            if gen_btn.is_visible():
                gen_btn.click()
                time.sleep(3)
                take_screenshot(page, "51_report_generated.png")

                # Scroll to see report details
                page.evaluate("window.scrollBy(0, 300)")
                time.sleep(1)
                take_screenshot(page, "52_report_details.png")

                # Scroll to XLSX button
                page.evaluate("window.scrollBy(0, 300)")
                time.sleep(1)
                take_screenshot(page, "53_report_xlsx.png")
        except Exception as e:
            print(f"  Report error: {e}")

        # ──────────────────────────────────────────────────
        # 6. EXPORT JE PAGE
        # ──────────────────────────────────────────────────
        print("\n6. Export JE page...")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)
        click_nav(page, "Export JE")
        wait_for_app(page, 3)
        take_screenshot(page, "60_export_je.png")

        # Click Validate & Preview
        print("  Clicking Validate & Preview...")
        try:
            val_btn = page.locator('button:has-text("Validate")').first
            if val_btn.is_visible():
                val_btn.click()
                time.sleep(3)
                take_screenshot(page, "61_export_validated.png")

                # Scroll to see CSV preview
                page.evaluate("window.scrollBy(0, 300)")
                time.sleep(1)
                take_screenshot(page, "62_export_csv_preview.png")

                # Scroll to download
                page.evaluate("window.scrollBy(0, 300)")
                time.sleep(1)
                take_screenshot(page, "63_export_download.png")
        except Exception as e:
            print(f"  Export error: {e}")

        # ──────────────────────────────────────────────────
        # 7. SAVE/LOAD in sidebar
        # ──────────────────────────────────────────────────
        print("\n7. Save/Load sidebar...")
        try:
            page.evaluate("""
                const sidebar = document.querySelector('[data-testid="stSidebar"]');
                if (sidebar) {
                    const scrollable = sidebar.querySelector('[data-testid="stSidebarContent"]') || sidebar;
                    scrollable.scrollTop = scrollable.scrollHeight;
                }
            """)
            time.sleep(1)
            sidebar = page.locator('[data-testid="stSidebar"]').first
            if sidebar.is_visible():
                sidebar.screenshot(path=os.path.join(SCREENSHOTS, "14_sidebar_save_load.png"))
                print("  Saved: 14_sidebar_save_load.png")
        except:
            pass

        browser.close()
        print("\nAll screenshots captured!")


if __name__ == "__main__":
    main()
