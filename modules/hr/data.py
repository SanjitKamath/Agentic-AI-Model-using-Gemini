import csv
import os

DB_PATH = os.path.join("data", "employees.csv")

def get_employee(employee_id: str):
    """
    Fetch employee data from CSV file.
    Returns a dict with employee details or None if not found.
    """
    with open(DB_PATH, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["employee_id"] == employee_id:
                return {
                    "employee_id": row["employee_id"],
                    "years_of_service": int(row["years_of_service"]),
                    "role_criticality": row["role_criticality"],
                    "performance": float(row["performance"]),
                }
    return None
