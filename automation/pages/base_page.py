"""Base Page Object class with shared navigation, wait, and screenshot utilities."""
from pathlib import Path
from typing import Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from config.settings import settings
from core.exceptions import NavigationError
from core.logger import RunLogger


class BasePage:
    """Foundational page object containing shared browser controls and screenshot mechanics."""

    def __init__(self, page: Page, logger: RunLogger, run_id: str):
        self.page = page
        self.logger = logger
        self.run_id = run_id

    def take_screenshot(self, step_name: str) -> Path:
        """Captures a timestamped step screenshot and stores it in the configured screenshots directory."""
        clean_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in step_name).strip("_")
        filename = f"{self.run_id}_{clean_name}.png"
        file_path = settings.screenshots_dir / filename
        
        try:
            self.page.screenshot(path=str(file_path), full_page=False)
            self.logger.debug(f"Saved step screenshot: {filename}", step=step_name)
        except Exception as e:
            self.logger.warning(f"Could not take screenshot for {step_name}: {e}", step=step_name)
            
        return file_path

    def navigate_to(self, url: str, wait_until: str = "load", timeout: int = 45000):
        """Navigates to the specified URL with timeout and logging."""
        self.logger.info(f"Navigating to {url}", step="Navigation")
        try:
            self.page.goto(url, wait_until=wait_until, timeout=timeout)
        except PlaywrightTimeoutError as e:
            self.take_screenshot("navigation_timeout")
            raise NavigationError(f"Timed out navigating to {url}: {e}", step="Navigation")
        except Exception as e:
            self.take_screenshot("navigation_error")
            raise NavigationError(f"Failed navigating to {url}: {e}", step="Navigation")

    def wait_for_visible(self, selector: str, timeout: int = 30000, step: str = "Wait"):
        """Waits for an element to become visible."""
        try:
            self.page.wait_for_selector(selector, state="visible", timeout=timeout)
        except PlaywrightTimeoutError as e:
            self.take_screenshot(f"wait_timeout_{step}")
            raise NavigationError(f"Element '{selector}' was not visible after {timeout}ms", step=step)

    def click_element(self, selector: str, step: str = "Click", timeout: int = 30000):
        """Waits for element and clicks it."""
        try:
            self.wait_for_visible(selector, timeout=timeout, step=step)
            self.page.click(selector, timeout=timeout)
        except Exception as e:
            self.take_screenshot(f"click_error_{step}")
            raise NavigationError(f"Failed to click '{selector}': {e}", step=step)

    def fill_input(self, selector: str, value: str, step: str = "Input", timeout: int = 30000):
        """Fills an input field with the provided value."""
        try:
            self.wait_for_visible(selector, timeout=timeout, step=step)
            self.page.fill(selector, value, timeout=timeout)
        except Exception as e:
            self.take_screenshot(f"fill_error_{step}")
            raise NavigationError(f"Failed to fill '{selector}': {e}", step=step)
