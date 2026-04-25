from enum import StrEnum


class MortgageRefusalReason(StrEnum):
    not_enough_income = "not_enough_income"
    not_enough_transactions = "not_enough_transactions"
    wrong_or_incomplete_documents = "wrong_or_incomplete_documents"


MORTGAGE_REFUSAL_REASON_LABELS = {
    MortgageRefusalReason.not_enough_income.value: "Not enough income",
    MortgageRefusalReason.not_enough_transactions.value: "Not enough transactions",
    MortgageRefusalReason.wrong_or_incomplete_documents.value: "Wrong / incomplete documents",
}

SUPPORTED_MORTGAGE_REFUSAL_REASONS = {r.value for r in MortgageRefusalReason}


def is_supported_mortgage_refusal_reason(value: str | None) -> bool:
    return value in SUPPORTED_MORTGAGE_REFUSAL_REASONS


def should_treat_as_mortgage_denial(
    subject: str,
    message: str,
    refusal_reason: str | None,
) -> bool:
    """Return True when the complaint should be handled as a mortgage-denial case."""
    if refusal_reason and is_supported_mortgage_refusal_reason(refusal_reason):
        return True
    text = (subject + " " + message).lower()
    return any(kw in text for kw in ("mortgage", "mortgage application", "mortgage rejection"))


def should_early_reject_mortgage_case(
    refusal_reason: str | None,
    extracted_data: dict,
) -> bool:
    """Return True when a mortgage-documents complaint should skip to a negative draft."""
    if refusal_reason != MortgageRefusalReason.wrong_or_incomplete_documents:
        return False
    if not extracted_data.get("is_relevant", True):
        return True
    missing = extracted_data.get("missing_documents", [])
    return len(missing) > 0


def get_expected_mortgage_category(refusal_reason: str | None = None) -> tuple[str, str]:
    if refusal_reason in MORTGAGE_REFUSAL_REASON_LABELS:
        return ("Mortgage Application Complaints", MORTGAGE_REFUSAL_REASON_LABELS[refusal_reason])
    return ("Other", "General Mortgage Application Complaint")


def get_mortgage_drafting_guidance(refusal_reason: str) -> str:
    guidance = {
        "not_enough_income": "Explain the income threshold used and what updated income evidence could support a new application.",
        "not_enough_transactions": "Explain the missing transaction history or salary activity and what account activity evidence is needed.",
        "wrong_or_incomplete_documents": "List the missing documents and invite the customer to resubmit a complete application package.",
    }
    return guidance.get(refusal_reason, "")
