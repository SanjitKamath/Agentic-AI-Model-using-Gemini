import pandas as pd

def check_loan_eligibility(
    customer_id: str,
    filepath: str = "data/bank_customers.csv",
    min_credit_score: int = 650,
    min_income: int = 50000,
    max_existing_loan: int = 20000
) -> dict:
    """
    Checks if a customer is eligible for a loan based on default or custom criteria.
    Reads customer data from a specified CSV file.
    """
    try:
        df = pd.read_csv(filepath)
        customer_data = df[df['customer_id'] == customer_id]

        if customer_data.empty:
            return {"error": f"Customer {customer_id} not found."}

        # Get the first row of customer data
        customer = customer_data.iloc[0]

        # Check criteria
        score_ok = customer["credit_score"] >= min_credit_score
        income_ok = customer["annual_income"] >= min_income
        loan_balance_ok = customer["existing_loan_balance"] <= max_existing_loan

        is_eligible = all([score_ok, income_ok, loan_balance_ok])

        reasons = {
            "credit_score_ok": bool(score_ok),
            "income_ok": bool(income_ok),
            "existing_loan_balance_ok": bool(loan_balance_ok)
        }

        return {
            "customer_id": customer_id,
            "eligible": bool(is_eligible),
            "checks": reasons
        }

    except FileNotFoundError:
        return {"error": f"Data file not found at: {filepath}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}