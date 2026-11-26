"""Orchestration runner executing the end-to-end OrangeHRM automation lifecycle."""
import argparse
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from playwright.sync_api import sync_playwright

from config.settings import settings
from core.exceptions import AutomationError
from core.logger import get_run_logger
from automation.pages.login_page import LoginPage
from automation.pages.dashboard_page import DashboardPage
from automation.pages.pim_page import PimPage
from automation.utils.exporter import export_employee_data


class AutomationRunner:
    """Executes the complete dashboard-driven RPA automation workflow."""

    def __init__(
        self,
        url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        employee_id: Optional[str] = None,
        middle_name: Optional[str] = None,
        headless: Optional[bool] = None,
        run_id: Optional[str] = None,
    ):
        self.run_id = run_id or f"run_{uuid.uuid4().hex[:8]}"
        self.url = url or settings.orangehrm_url
        self.username = username or settings.default_username
        self.password = password or settings.default_password
        self.first_name = first_name or "AutoTester"
        self.last_name = last_name or f"User{int(time.time()) % 1000}"
        self.employee_id = employee_id
        self.middle_name = middle_name or ""
        self.headless = headless if headless is not None else settings.headless
        
        self.logger = get_run_logger(self.run_id)
        self.screenshots: List[str] = []

    def execute(self) -> Dict[str, Any]:
        """Runs the entire automation flow and returns execution metrics and results."""
        start_time = time.time()
        self.logger.info(f"=== Starting Automation Run [{self.run_id}] ===", step="Init")
        self.logger.info(
            f"Target URL: {self.url} | Username: {self.username} | Headless: {self.headless}",
            step="Init",
        )

        result: Dict[str, Any] = {
            "run_id": self.run_id,
            "status": "RUNNING",
            "inserted_employee": None,
            "extracted_count": 0,
            "extracted_data": [],
            "csv_path": None,
            "excel_path": None,
            "screenshots": [],
            "error": None,
            "start_time": datetime.now().isoformat(),
            "duration_seconds": 0.0,
        }

        try:
            with sync_playwright() as playwright:
                self.logger.info("Launching Chrome browser engine...", step="Browser Init")
                browser = playwright.chromium.launch(
                    channel=settings.browser_channel,
                    headless=self.headless,
                    args=["--no-sandbox", "--disable-dev-shm-usage"],
                )
                
                context = browser.new_context(
                    viewport={"width": 1440, "height": 900},
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                )
                page = context.new_page()
                page.set_default_timeout(settings.browser_timeout_ms)

                # Initialize Page Objects
                login_page = LoginPage(page, self.logger, self.run_id)
                dashboard_page = DashboardPage(page, self.logger, self.run_id)
                pim_page = PimPage(page, self.logger, self.run_id)

                # Step 1: Open OrangeHRM
                self.logger.info("Step 1/7: Opening OrangeHRM portal", step="Step 1: Open Portal")
                login_page.open(self.url)

                # Step 2: Login with provided credentials
                self.logger.info("Step 2/7: Authenticating with dashboard credentials", step="Step 2: Login")
                login_page.login(self.username, self.password)

                # Step 3: Navigate to PIM module
                self.logger.info("Step 3/7: Navigating to PIM section", step="Step 3: Navigate PIM")
                dashboard_page.verify_landing()
                dashboard_page.navigate_to_pim()

                # Step 4: Add New Employee
                self.logger.info("Step 4/7: Adding new employee", step="Step 4: Add Employee")
                pim_page.open_add_employee_form()
                submitted_employee = pim_page.add_employee(
                    first_name=self.first_name,
                    last_name=self.last_name,
                    employee_id=self.employee_id,
                    middle_name=self.middle_name,
                )

                # Step 5: Verify Employee Creation Success
                self.logger.info("Step 5/7: Verifying employee creation", step="Step 5: Verify Creation")
                verified_employee = pim_page.verify_employee_created(submitted_employee)
                result["inserted_employee"] = verified_employee
                self.logger.info(f"Verified created employee: {verified_employee}", step="Step 5: Verify Creation")

                # Step 6: Extract Employee List Data & Export
                self.logger.info("Step 6/7: Extracting employee list data", step="Step 6: Extract Data")
                extracted_data = pim_page.extract_employee_list(max_records=50)
                result["extracted_count"] = len(extracted_data)
                result["extracted_data"] = extracted_data

                # Export to CSV and Excel
                self.logger.info("Exporting extracted records to CSV and Excel...", step="Export Data")
                csv_path, excel_path = export_employee_data(extracted_data, self.run_id)
                result["csv_path"] = str(csv_path)
                result["excel_path"] = str(excel_path)
                result["csv_filename"] = csv_path.name
                result["excel_filename"] = excel_path.name
                self.logger.info(f"Generated CSV: {csv_path.name} | Excel: {excel_path.name}", step="Export Data")

                # Step 7: Clean Logout
                self.logger.info("Step 7/7: Performing application logout", step="Step 7: Logout")
                dashboard_page.logout()

                # Cleanly shut down browser
                context.close()
                browser.close()

            # Collect generated screenshots for this run
            screenshot_files = sorted(settings.screenshots_dir.glob(f"{self.run_id}_*.png"))
            result["screenshots"] = [p.name for p in screenshot_files]

            result["status"] = "SUCCESS"
            self.logger.info(
                f"=== Automation Run [{self.run_id}] Completed Successfully ===",
                step="Complete",
            )

        except AutomationError as e:
            result["status"] = "FAILED"
            result["error"] = e.to_dict()
            self.logger.error(f"Automation failed at [{e.step}]: {e.message}", step=e.step)
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = {"error_type": type(e).__name__, "message": str(e), "step": "Execution"}
            self.logger.error(f"Unexpected error during automation: {e}", step="Fatal Error")
        finally:
            result["duration_seconds"] = round(time.time() - start_time, 2)
            # Collect any screenshots created up to the failure point
            screenshot_files = sorted(settings.screenshots_dir.glob(f"{self.run_id}_*.png"))
            result["screenshots"] = [p.name for p in screenshot_files]

        return result


def main():
    """Command-line entrypoint for AutomationRunner."""
    parser = argparse.ArgumentParser(description="Run OrangeHRM RPA Automation")
    parser.add_argument("--url", default=settings.orangehrm_url, help="OrangeHRM URL")
    parser.add_argument("--username", default=settings.default_username, help="Username")
    parser.add_argument("--password", default=settings.default_password, help="Password")
    parser.add_argument("--first-name", default="AutoTest", help="Employee First Name")
    parser.add_argument("--last-name", default="Engineer", help="Employee Last Name")
    parser.add_argument("--emp-id", default=None, help="Employee ID (optional)")
    parser.add_argument("--middle-name", default="", help="Employee Middle Name")
    parser.add_argument("--headless", action="store_true", default=True, help="Run headless")
    parser.add_argument("--headed", dest="headless", action="store_false", help="Run headed")

    args = parser.parse_args()

    runner = AutomationRunner(
        url=args.url,
        username=args.username,
        password=args.password,
        first_name=args.first_name,
        last_name=args.last_name,
        employee_id=args.emp_id,
        middle_name=args.middle_name,
        headless=args.headless,
    )

    res = runner.execute()
    print("\n--- Execution Summary ---")
    print(f"Status: {res['status']}")
    print(f"Duration: {res['duration_seconds']}s")
    if res['status'] == 'SUCCESS':
        print(f"Created: {res['inserted_employee']}")
        print(f"Extracted Records: {res['extracted_count']}")
        print(f"CSV Export: {res['csv_path']}")
        print(f"Excel Export: {res['excel_path']}")
        sys.exit(0)
    else:
        print(f"Error: {res['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
