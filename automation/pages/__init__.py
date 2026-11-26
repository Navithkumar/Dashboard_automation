"""Page Object Model (POM) representations for OrangeHRM pages."""
from automation.pages.base_page import BasePage
from automation.pages.login_page import LoginPage
from automation.pages.dashboard_page import DashboardPage
from automation.pages.pim_page import PimPage

__all__ = ["BasePage", "LoginPage", "DashboardPage", "PimPage"]
