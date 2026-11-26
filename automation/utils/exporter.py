"""Export utilities for extracted employee records to CSV and Excel."""
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
from config.settings import settings


def export_employee_data(
    records: List[Dict[str, str]],
    run_id: str,
    output_dir: Path | None = None,
) -> Tuple[Path, Path]:
    """
    Exports employee records to both CSV and Excel formats.
    
    Returns:
        Tuple[Path, Path]: (csv_path, excel_path)
    """
    target_dir = output_dir or settings.data_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"employees_{run_id}_{timestamp}.csv"
    excel_filename = f"employees_{run_id}_{timestamp}.xlsx"

    csv_path = target_dir / csv_filename
    excel_path = target_dir / excel_filename

    if not records:
        # Create empty template with expected columns
        columns = [
            "Employee ID",
            "First & Middle Name",
            "Last Name",
            "Job Title",
            "Employment Status",
            "Sub Unit",
            "Supervisor",
        ]
        df = pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(records)

    # Export to CSV
    df.to_csv(csv_path, index=False, encoding="utf-8")

    # Export to Excel using openpyxl
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="OrangeHRM Employees")

    return csv_path, excel_path
