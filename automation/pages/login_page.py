"""Page Object for OrangeHRM Authentication / Login Page."""
from automation.pages.base_page import BasePage
from core.exceptions import AuthenticationError


class LoginPage(BasePage):
    """Encapsulates OrangeHRM login view selectors and actions."""

    # Selectors
    USERNAME_INPUT = 'input[name="username"]'
    PASSWORD_INPUT = 'input[name="password"]'
    SUBMIT_BUTTON = 'button[type="submit"]'
    ERROR_ALERT = '.oxd-alert-content-text'
    LOGIN_TITLE = '.orangehrm-login-title'

    def open(self, base_url: str):
        """Opens OrangeHRM login page and verifies visibility of form."""
        login_url = base_url.rstrip("/") + "/web/index.php/auth/login"
        self.navigate_to(login_url)
        self.wait_for_visible(self.USERNAME_INPUT, step="Open Login Page")
        self.take_screenshot("01_login_page_loaded")
        self.logger.info("Login page opened and elements ready", step="Login")

    def login(self, username: str, password: str):
        """Submits credentials and handles validation."""
        self.logger.info(f"Submitting login credentials for user '{username}'", step="Login")
        
        self.fill_input(self.USERNAME_INPUT, username, step="Enter Username")
        self.fill_input(self.PASSWORD_INPUT, password, step="Enter Password")
        self.take_screenshot("02_credentials_entered")
        
        self.click_element(self.SUBMIT_BUTTON, step="Submit Login")

        # Check for immediate invalid credentials alert
        try:
            self.page.wait_for_selector(self.ERROR_ALERT, timeout=4000)
            error_text = self.page.locator(self.ERROR_ALERT).inner_text().strip()
            self.take_screenshot("login_failed_alert")
            raise AuthenticationError(f"Login rejected by OrangeHRM: {error_text}")
        except AuthenticationError:
            raise
        except Exception:
            # No error alert within 4s, proceeding to wait for dashboard
            pass

        # Wait for redirection away from login page to dashboard
        try:
            self.page.wait_for_url("**/dashboard/**", timeout=30000)
            self.logger.info("Authentication successful. Redirected to Dashboard.", step="Login")
            self.take_screenshot("03_login_successful")
        except Exception as e:
            self.take_screenshot("login_timeout_error")
            raise AuthenticationError(f"Failed to reach dashboard after login: {e}")
