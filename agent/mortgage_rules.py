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


def is_customer_evidence_category(category: str | None) -> bool:
    """Return True when the category indicates the customer submitted counter-evidence."""
    return bool(category and "customer provides" in category.lower())


def get_customer_evidence_drafting_guidance(refusal_reason: str | None) -> str:
    """Return extra drafting guidance for cases where the customer submitted supporting documents."""
    guidance = {
        "not_enough_income": (
            "The customer has submitted income evidence to contest the refusal. "
            "Acknowledge the documents received. "
            "If the decision is POSITIVE, confirm that the evidence demonstrates sufficient income and the application will proceed. "
            "If the decision is NEGATIVE, explain specifically why the submitted documents are still insufficient against the bank's income threshold."
        ),
        "not_enough_transactions": (
            "The customer has submitted transaction history to contest the refusal. "
            "Acknowledge the documents received. "
            "If the decision is POSITIVE, confirm that the submitted transaction history meets the bank's requirements and the application will proceed. "
            "If the decision is NEGATIVE, explain specifically what transaction activity is still missing or insufficient."
        ),
        "wrong_or_incomplete_documents": (
            "The customer has resubmitted documentation to contest the refusal. "
            "Acknowledge the documents received. "
            "If the decision is POSITIVE, confirm that the documentation is now complete and the application will be reviewed. "
            "If the decision is NEGATIVE, clearly list which required documents are still missing or do not meet requirements."
        ),
    }
    return guidance.get(refusal_reason or "", (
        "The customer has submitted supporting documents to contest the decision. "
        "Acknowledge the evidence provided and explain how it was evaluated in the decision."
    ))
