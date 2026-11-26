"""Page Object for OrangeHRM PIM (Employee Operations & Extraction)."""
import time
from typing import Dict, List, Optional
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from automation.pages.base_page import BasePage
from core.exceptions import EmployeeCreationError, DataExtractionError


class PimPage(BasePage):
    """Encapsulates PIM features: Add Employee, Verification, and Table Extraction."""

    # Selectors
    ADD_EMPLOYEE_NAV = 'a:has-text("Add Employee")'
    EMPLOYEE_LIST_NAV = 'a:has-text("Employee List")'
    FIRST_NAME_INPUT = 'input[name="firstName"]'
    MIDDLE_NAME_INPUT = 'input[name="middleName"]'
    LAST_NAME_INPUT = 'input[name="lastName"]'
    EMP_ID_INPUT = 'div:has(> label:has-text("Employee Id")) + div input'
    SAVE_BUTTON = 'button[type="submit"]'
    SUCCESS_TOAST = '.oxd-toast--success'
    TABLE_BODY = '.oxd-table-body'
    TABLE_ROW = '.oxd-table-row'
    TABLE_CELL = '.oxd-table-cell'

    def open_add_employee_form(self):
        """Navigates to the Add Employee page."""
        self.logger.info("Opening Add Employee form", step="Add Employee")
        self.click_element(self.ADD_EMPLOYEE_NAV, step="Click Add Employee Tab")
        self.wait_for_visible(self.FIRST_NAME_INPUT, step="Wait Add Form Loaded")
        self.take_screenshot("06_add_employee_opened")

    def add_employee(
        self,
        first_name: str,
        last_name: str,
        employee_id: Optional[str] = None,
        middle_name: Optional[str] = "",
    ) -> Dict[str, str]:
        """Fills and submits new employee data, returning submitted credentials."""
        self.logger.info(
            f"Entering employee details: Name='{first_name} {last_name}', Employee ID='{employee_id or 'Auto'}'",
            step="Add Employee",
        )

        self.fill_input(self.FIRST_NAME_INPUT, first_name, step="Enter First Name")
        if middle_name:
            self.fill_input(self.MIDDLE_NAME_INPUT, middle_name, step="Enter Middle Name")
        self.fill_input(self.LAST_NAME_INPUT, last_name, step="Enter Last Name")

        # Set or read Employee ID
        id_locator = self.page.locator(self.EMP_ID_INPUT)
        id_locator.wait_for(state="visible", timeout=15000)
        
        final_emp_id = employee_id
        if final_emp_id and final_emp_id.strip():
            id_locator.click()
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
            id_locator.fill(final_emp_id.strip())
        else:
            final_emp_id = id_locator.input_value().strip()

        self.take_screenshot("07_employee_details_filled")
        self.logger.info(f"Submitting employee registration with ID: {final_emp_id}", step="Add Employee")
        
        self.click_element(self.SAVE_BUTTON, step="Click Save Employee")

        return {
            "first_name": first_name,
            "middle_name": middle_name or "",
            "last_name": last_name,
            "employee_id": final_emp_id,
        }

    def verify_employee_created(self, submitted_data: Dict[str, str]) -> Dict[str, str]:
        """Verifies that employee creation succeeded via toast notification and personal details redirection."""
        self.logger.info("Verifying employee creation status...", step="Verify Employee")
        
        toast_detected = False
        try:
            self.page.wait_for_selector(self.SUCCESS_TOAST, timeout=12000)
            toast_text = self.page.locator(self.SUCCESS_TOAST).inner_text().replace("\n", " ").strip()
            self.logger.info(f"Success toast detected: '{toast_text}'", step="Verify Employee")
            toast_detected = True
        except PlaywrightTimeoutError:
            self.logger.warning("Toast notification timed out, checking redirection...", step="Verify Employee")

        try:
            # OrangeHRM redirects to viewPersonalDetails/empNumber/<number> upon creation
            self.page.wait_for_url("**/pim/viewPersonalDetails/**", timeout=30000)
            current_url = self.page.url
            self.logger.info(f"Confirmed redirection to Personal Details: {current_url}", step="Verify Employee")
        except Exception as e:
            self.take_screenshot("verification_redirect_failed")
            if not toast_detected:
                raise EmployeeCreationError(f"Employee creation could not be verified: {e}")

        self.take_screenshot("08_employee_verified_success")
        
        result_data = dict(submitted_data)
        result_data["status"] = "Verified"
        result_data["verified_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        return result_data

    def extract_employee_list(self, max_records: int = 50) -> List[Dict[str, str]]:
        """Navigates to Employee List and extracts tabular employee records."""
        self.logger.info("Navigating to Employee List to extract records", step="Extract Data")
        self.click_element(self.EMPLOYEE_LIST_NAV, step="Click Employee List Tab")
        
        try:
            self.page.wait_for_selector(self.TABLE_BODY, state="visible", timeout=30000)
        except Exception as e:
            self.take_screenshot("table_not_loaded")
            raise DataExtractionError(f"Employee table was not rendered: {e}")

        # Small wait for rows to populate
        self.page.wait_for_timeout(1500)
        
        row_elements = self.page.locator(f"{self.TABLE_BODY} {self.TABLE_ROW}").all()
        self.logger.info(f"Found {len(row_elements)} rows in employee table", step="Extract Data")

        records: List[Dict[str, str]] = []
        for i, row in enumerate(row_elements[:max_records]):
            cells = row.locator(self.TABLE_CELL).all()
            # Standard OrangeHRM row layout:
            # Cell 0: Checkbox
            # Cell 1: ID
            # Cell 2: First (& Middle) Name
            # Cell 3: Last Name
            # Cell 4: Job Title
            # Cell 5: Employment Status
            # Cell 6: Sub Unit
            # Cell 7: Supervisor
            cell_texts = [cell.inner_text().strip() for cell in cells]
            
            if len(cell_texts) >= 4:
                record = {
                    "employee_id": cell_texts[1] if len(cell_texts) > 1 else "",
                    "first_name": cell_texts[2] if len(cell_texts) > 2 else "",
                    "last_name": cell_texts[3] if len(cell_texts) > 3 else "",
                    "job_title": cell_texts[4] if len(cell_texts) > 4 else "",
                    "employment_status": cell_texts[5] if len(cell_texts) > 5 else "",
                    "sub_unit": cell_texts[6] if len(cell_texts) > 6 else "",
                    "supervisor": cell_texts[7] if len(cell_texts) > 7 else "",
                }
                records.append(record)

        self.take_screenshot("09_employee_data_extracted")
        self.logger.info(f"Extracted {len(records)} employee records successfully", step="Extract Data")
        return records
