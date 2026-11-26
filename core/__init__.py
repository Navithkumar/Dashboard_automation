"""Core functionality including logging and exceptions."""
from core.exceptions import (
    AutomationError,
    AuthenticationError,
    NavigationError,
    EmployeeCreationError,
    DataExtractionError,
)
from core.logger import setup_logger, get_run_logger, LogBroadcaster

__all__ = [
    "AutomationError",
    "AuthenticationError",
    "NavigationError",
    "EmployeeCreationError",
    "DataExtractionError",
    "setup_logger",
    "get_run_logger",
    "LogBroadcaster",
]
