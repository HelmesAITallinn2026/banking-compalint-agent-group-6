from data_retrieval_agent.mortgage_mock_data import build_mortgage_assessment


def test_income_reason_returns_income_threshold_context():
    assessment = build_mortgage_assessment("cmp123", "not_enough_income")
    assert "monthly_income" in assessment
    assert "minimum_income_required" in assessment


def test_transaction_reason_returns_transaction_context():
    assessment = build_mortgage_assessment("cmp123", "not_enough_transactions")
    assert "eligible_transaction_count" in assessment
    assert "minimum_transaction_count" in assessment


def test_documents_reason_returns_missing_docs():
    assessment = build_mortgage_assessment("cmp123", "wrong_or_incomplete_documents")
    assert "missing_documents" in assessment
    assert len(assessment["missing_documents"]) > 0
