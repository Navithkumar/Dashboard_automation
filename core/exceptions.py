"""Custom domain exceptions for Dashboard Automation."""


class AutomationError(Exception):
    """Base exception for all automation failures."""

    def __init__(self, message: str, step: str = "Unknown", details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.step = step
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "step": self.step,
            "details": self.details,
        }


class AuthenticationError(AutomationError):
    """Raised when login or credentials verification fails."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, step="Login", details=details)


class NavigationError(AutomationError):
    """Raised when page navigation fails or target element cannot be reached."""

    def __init__(self, message: str, step: str = "Navigation", details: dict | None = None):
        super().__init__(message, step=step, details=details)


class EmployeeCreationError(AutomationError):
    """Raised when employee creation fails or cannot be verified."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, step="Add Employee", details=details)


class DataExtractionError(AutomationError):
    """Raised when extracting employee list data fails."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, step="Extract Data", details=details)
