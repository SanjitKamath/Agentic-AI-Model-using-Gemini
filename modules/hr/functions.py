import pandas as pd

EMPLOYEE_DB = "data/employees.csv"

def load_employee_data():
    """Load employee data from CSV"""
    return pd.read_csv(EMPLOYEE_DB)

def check_eligibility(employee_id: str) -> dict:
    """Check eligibility for a raise"""
    df = load_employee_data()
    emp = df[df['employee_id'] == employee_id]

    if emp.empty:
        return {"eligible": False, "reason": "Employee not found"}

    emp = emp.iloc[0]
    eligible = (emp["years_experience"] >= 2 and
                emp["role_criticality"] == "high" and
                emp["performance_score"] >= 85)

    return {
        "eligible": bool(eligible),
        "employee_id": employee_id,
        "years_experience": int(emp["years_experience"]),
        "role_criticality": emp["role_criticality"],
        "performance_score": int(emp["performance_score"]),
        "reason": "Meets criteria" if eligible else "Does not meet all criteria"
    }

def calculate_raise(employee_id: str) -> dict:
    """Calculate raise % based on performance and role criticality"""
    df = load_employee_data()
    emp = df[df['employee_id'] == employee_id]

    if emp.empty:
        return {"raise_percent": 0, "reason": "Employee not found"}

    emp = emp.iloc[0]

    if emp["performance_score"] > 90 and emp["role_criticality"] == "high":
        raise_percent = 12
    elif emp["performance_score"] > 80:
        raise_percent = 8
    else:
        raise_percent = 5

    return {
        "employee_id": employee_id,
        "raise_percent": int(raise_percent),
        "reason": "Based on performance and role criticality"
    }

def custom_eligibility_check(employee_id: str, experience: int = 0, criticality: str = "any", performance_score: int = 0) -> dict:
    """Check for eligibility using custom, user-defined criteria."""
    df = load_employee_data()
    emp = df[df['employee_id'] == employee_id]

    if emp.empty:
        return {"eligible": False, "reason": "Employee not found"}

    emp = emp.iloc[0]

    # Safely get values from the DataFrame, treating missing data as 0 or empty string
    actual_experience = emp["years_experience"] if pd.notna(emp["years_experience"]) else 0
    actual_performance = emp["performance_score"] if pd.notna(emp["performance_score"]) else 0
    actual_criticality = emp["role_criticality"].lower() if pd.notna(emp["role_criticality"]) else ""

    # Check each condition against the provided arguments
    cond_experience = actual_experience >= experience
    cond_criticality = criticality.lower() == 'any' or actual_criticality == criticality.lower()
    cond_performance = actual_performance >= performance_score

    eligible = all([cond_experience, cond_criticality, cond_performance])

    reason = "Meets the custom criteria." if eligible else "Does not meet all of the custom criteria provided."

    return {
        "employee_id": employee_id,
        "eligible": bool(eligible),
        "reason": reason
    }