"""Pydantic request and response schemas for Dashboard API."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AutomationRequest(BaseModel):
    """Payload received from the frontend dashboard when triggering automation."""

    url: Optional[str] = Field(
        default="https://opensource-demo.orangehrmlive.com",
        description="Target OrangeHRM base URL",
    )
    username: str = Field(default="Admin", min_length=1, description="OrangeHRM Login Username")
    password: str = Field(default="admin123", min_length=1, description="OrangeHRM Login Password")
    first_name: str = Field(..., min_length=1, description="Employee First Name")
    last_name: str = Field(..., min_length=1, description="Employee Last Name")
    middle_name: Optional[str] = Field(default="", description="Employee Middle Name (Optional)")
    employee_id: Optional[str] = Field(default="", description="Employee ID (Optional, generated if empty)")
    headless: bool = Field(default=True, description="Whether browser runs in headless mode")


class InsertedEmployee(BaseModel):
    first_name: str
    middle_name: Optional[str] = ""
    last_name: str
    employee_id: str
    status: str = "Verified"
    verified_at: Optional[str] = None


class AutomationResponse(BaseModel):
    """Response returned upon completion or status polling."""

    run_id: str
    status: str
    inserted_employee: Optional[Dict[str, Any]] = None
    extracted_count: int = 0
    extracted_data: List[Dict[str, Any]] = []
    csv_filename: Optional[str] = None
    excel_filename: Optional[str] = None
    screenshots: List[str] = []
    duration_seconds: float = 0.0
    error: Optional[Dict[str, Any]] = None


class RunStatusResponse(BaseModel):
    run_id: str
    status: str
    message: Optional[str] = None
