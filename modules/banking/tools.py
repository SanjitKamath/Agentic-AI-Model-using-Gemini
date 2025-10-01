from agent.registry import register
from .functions import check_loan_eligibility

@register(
    name="check_loan_eligibility",
    description="..." # Your existing description
)
def decorated_check_loan_eligibility(
    customer_id: str,
    filepath: str = "data/bank_customers.csv", # <-- Add filepath here too
    min_credit_score: int = 650,
    min_income: int = 50000,
    max_existing_loan: int = 20000
) -> dict:
    return check_loan_eligibility(
        customer_id, filepath, min_credit_score, min_income, max_existing_loan
    )