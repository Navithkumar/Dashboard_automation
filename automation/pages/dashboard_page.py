"""Page Object for OrangeHRM Dashboard Navigation and User Dropdown."""
from automation.pages.base_page import BasePage
from core.exceptions import NavigationError


class DashboardPage(BasePage):
    """Handles top-level dashboard operations and navigation."""

    # Selectors
    PIM_MENU_LINK = 'a[href*="viewPimModule"]'
    USER_DROPDOWN = '.oxd-userdropdown-tab'
    LOGOUT_LINK = 'a:has-text("Logout")'
    TOPBAR_HEADER = '.oxd-topbar-header-breadcrumb'

    def verify_landing(self):
        """Verifies dashboard is fully rendered."""
        self.wait_for_visible(self.TOPBAR_HEADER, step="Verify Dashboard")
        self.logger.info("OrangeHRM Dashboard confirmed ready", step="Dashboard")
        self.take_screenshot("04_dashboard_ready")

    def navigate_to_pim(self):
        """Clicks PIM module link and waits for PIM view."""
        self.logger.info("Navigating to PIM (Personnel Information Management) module", step="PIM Navigation")
        self.click_element(self.PIM_MENU_LINK, step="Click PIM Link")
        
        try:
            self.page.wait_for_url("**/pim/**", timeout=30000)
            self.logger.info("Successfully arrived at PIM module", step="PIM Navigation")
            self.take_screenshot("05_pim_module_opened")
        except Exception as e:
            self.take_screenshot("pim_navigation_error")
            raise NavigationError(f"Failed to navigate to PIM module: {e}", step="PIM Navigation")

    def logout(self):
        """Performs clean logout via user dropdown."""
        self.logger.info("Initiating logout sequence", step="Logout")
        self.click_element(self.USER_DROPDOWN, step="Open User Dropdown")
        self.wait_for_visible(self.LOGOUT_LINK, timeout=10000, step="Wait Logout Option")
        self.take_screenshot("10_logout_menu_opened")
        
        self.click_element(self.LOGOUT_LINK, step="Click Logout")
        
        try:
            self.page.wait_for_url("**/auth/login", timeout=30000)
            self.logger.info("Clean logout verified. Returned to login page.", step="Logout")
            self.take_screenshot("11_logout_completed")
        except Exception as e:
            self.take_screenshot("logout_error")
            raise NavigationError(f"Failed to verify logout redirection: {e}", step="Logout")
