from agent.registry import register
from .functions import check_loan_eligibility

@register(
    name="check_loan_eligibility",
    description="Determines if a bank customer is eligible for a loan. Use for questions like 'Is customer B005 eligible for a loan?' or 'Can B099 get a loan with a credit score of 700?'"
)
def decorated_check_loan_eligibility(
    customer_id: str,
    filepath: str = "data/bank_customers.csv",
    min_credit_score: int = 650,
    min_income: int = 50000,
    max_existing_loan: int = 20000
) -> dict:
    """
    Registers the loan eligibility function as a tool for the agent.
    """
    return check_loan_eligibility(
        customer_id, 
        filepath, 
        min_credit_score, 
        min_income, 
        max_existing_loan
    )