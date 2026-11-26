"""Automated test suite for OrangeHRM RPA Dashboard."""
import tempfile
from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from config.settings import settings
from core.exceptions import (
    AutomationError,
    AuthenticationError,
    NavigationError,
    EmployeeCreationError,
    DataExtractionError,
)
from automation.utils.exporter import export_employee_data

client = TestClient(app)


def test_settings_initialization():
    """Verify configuration settings and directory resolution."""
    assert settings.orangehrm_url.startswith("https://")
    assert settings.default_username == "Admin"
    assert settings.output_dir.exists()
    assert settings.data_dir.exists()
    assert settings.logs_dir.exists()
    assert settings.screenshots_dir.exists()


def test_exporter_csv_and_excel():
    """Verify CSV and Excel generation for employee records."""
    sample_records = [
        {
            "employee_id": "EMP101",
            "first_name": "Alice",
            "last_name": "Smith",
            "job_title": "QA Engineer",
            "employment_status": "Full-Time",
            "sub_unit": "Engineering",
            "supervisor": "Bob Jones",
        },
        {
            "employee_id": "EMP102",
            "first_name": "Charlie",
            "last_name": "Brown",
            "job_title": "Developer",
            "employment_status": "Full-Time",
            "sub_unit": "Engineering",
            "supervisor": "Alice Smith",
        },
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        csv_path, excel_path = export_employee_data(sample_records, "test_run", output_dir=tmp_path)

        assert csv_path.exists()
        assert excel_path.exists()
        assert csv_path.suffix == ".csv"
        assert excel_path.suffix == ".xlsx"

        # Verify CSV content
        df_csv = pd.read_csv(csv_path)
        assert len(df_csv) == 2
        assert "EMP101" in df_csv["employee_id"].values
        assert "EMP102" in df_csv["employee_id"].values

        # Verify Excel content
        df_excel = pd.read_excel(excel_path)
        assert len(df_excel) == 2
        assert "Alice" in df_excel["first_name"].values


def test_custom_exceptions():
    """Verify domain exception hierarchy and formatting."""
    err = AuthenticationError("Invalid login credentials", details={"user": "tester"})
    assert isinstance(err, AutomationError)
    assert err.step == "Login"
    data = err.to_dict()
    assert data["error_type"] == "AuthenticationError"
    assert data["message"] == "Invalid login credentials"
    assert data["details"]["user"] == "tester"


def test_api_index_page():
    """Verify web dashboard HTML template loads."""
    response = client.get("/")
    assert response.status_code == 200
    assert "OrangeHRM" in response.text
    assert "Trigger Automation" in response.text


def test_api_validation_failure():
    """Verify validation error when required fields are missing."""
    invalid_payload = {
        "first_name": "",  # Empty first name violates min_length=1
        "last_name": "Tester",
    }
    response = client.post("/api/run-automation", json=invalid_payload)
    assert response.status_code == 422


def test_api_runs_list():
    """Verify listing runs returns a JSON list."""
    response = client.get("/api/runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_download_invalid_type():
    """Verify 400 rejection for invalid file types."""
    response = client.get("/api/download/pdf/somefile.pdf")
    assert response.status_code == 400


def test_api_download_missing_file():
    """Verify 404 rejection for nonexistent file."""
    response = client.get("/api/download/csv/nonexistent_file_9999.csv")
    assert response.status_code == 404
