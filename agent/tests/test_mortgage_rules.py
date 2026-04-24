from mortgage_rules import (
    get_expected_mortgage_category,
    get_mortgage_drafting_guidance,
    is_supported_mortgage_refusal_reason,
    should_early_reject_mortgage_case,
    should_treat_as_mortgage_denial,
)


def test_supported_reasons_accepted():
    assert is_supported_mortgage_refusal_reason("not_enough_income")
    assert is_supported_mortgage_refusal_reason("not_enough_transactions")
    assert is_supported_mortgage_refusal_reason("wrong_or_incomplete_documents")


def test_unsupported_reason_rejected():
    assert not is_supported_mortgage_refusal_reason("property_value_too_low")
    assert not is_supported_mortgage_refusal_reason(None)
    assert not is_supported_mortgage_refusal_reason("")


def test_detects_mortgage_denial_from_message_and_refusal_reason():
    assert should_treat_as_mortgage_denial(
        subject="Mortgage rejection",
        message="My mortgage application was refused because my income is too low.",
        refusal_reason="not_enough_income",
    )


def test_detects_mortgage_from_text_alone():
    assert should_treat_as_mortgage_denial(
        subject="Mortgage issue",
        message="My mortgage was rejected.",
        refusal_reason=None,
    )


def test_non_mortgage_not_detected():
    assert not should_treat_as_mortgage_denial(
        subject="Card dispute",
        message="I was charged twice.",
        refusal_reason=None,
    )


def test_only_early_rejects_mortgage_case_when_documents_are_incomplete():
    assert should_early_reject_mortgage_case(
        refusal_reason="wrong_or_incomplete_documents",
        extracted_data={"missing_documents": ["salary_statement"], "is_relevant": True},
    )


def test_no_early_reject_for_income_reason():
    assert not should_early_reject_mortgage_case(
        refusal_reason="not_enough_income",
        extracted_data={"missing_documents": [], "is_relevant": True},
    )


def test_expected_mortgage_category_points_to_mortgage_rejection():
    assert get_expected_mortgage_category() == (
        "Loan Complaints",
        "Mortgage Application Rejection",
    )


def test_documents_reason_includes_missing_document_guidance():
    guidance = get_mortgage_drafting_guidance("wrong_or_incomplete_documents")
    assert "missing documents" in guidance.lower()


def test_income_reason_includes_income_guidance():
    guidance = get_mortgage_drafting_guidance("not_enough_income")
    assert "income" in guidance.lower()


def test_transaction_reason_includes_transaction_guidance():
    guidance = get_mortgage_drafting_guidance("not_enough_transactions")
    assert "transaction" in guidance.lower()
