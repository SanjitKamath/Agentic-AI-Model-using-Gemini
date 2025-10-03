from agent.registry import register
# Use a relative import to get functions from the same module
from .functions import check_eligibility, calculate_raise, load_employee_data, custom_eligibility_check

@register(
    name="check_eligibility",
    description="Checks if an employee is eligible for a standard raise. Use for queries like 'is emp-123 eligible for a raise?' or 'check raise eligibility for emp-456'.",
)
def decorated_check_eligibility(employee_id: str) -> dict:
    return check_eligibility(employee_id)

@register(
    name="is_eligible_for_raise",
    description="Checks if an employee is eligible for a standard raise. This is an alias for check_eligibility.",
)
def decorated_is_eligible_for_raise(employee_id: str) -> dict:
    """This is an alias and calls the main eligibility function."""
    return check_eligibility(employee_id)

@register(
    name="calculate_raise",
    description="Calculate the percentage raise for an employee based on performance and role.",
)
def decorated_calculate_raise(employee_id: str) -> dict:
    return calculate_raise(employee_id)

@register(
    name="load_employee_data",
    description="Load and view the entire employee dataset.",
)
def decorated_load_employee_data():
    df = load_employee_data()
    return df.to_json(orient='records')

@register(
    name="custom_eligibility_check",
    description="Check if an employee is eligible based on custom criteria. The 'criticality' parameter accepts 'high', 'medium', or 'low'.",
)
def decorated_custom_check(employee_id: str, experience: int = 0, criticality: str = "any", performance_score: int = 0) -> dict:
    return custom_eligibility_check(employee_id, experience, criticality, performance_score)