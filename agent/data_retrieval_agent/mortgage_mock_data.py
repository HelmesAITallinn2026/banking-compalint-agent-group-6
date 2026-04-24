from __future__ import annotations


def build_mortgage_assessment(complaint_id: str, refusal_reason: str) -> dict:
    """Return mock underwriting data keyed to the mortgage refusal reason."""
    if refusal_reason == "not_enough_income":
        return {
            "monthly_income": 2400,
            "minimum_income_required": 3200,
            "debt_to_income_ratio": 0.58,
        }
    if refusal_reason == "not_enough_transactions":
        return {
            "eligible_transaction_count": 2,
            "minimum_transaction_count": 6,
            "salary_payment_detected": False,
        }
    # wrong_or_incomplete_documents
    return {
        "required_documents": ["id_copy", "salary_statement", "bank_statement"],
        "provided_documents": ["id_copy"],
        "missing_documents": ["salary_statement", "bank_statement"],
    }
