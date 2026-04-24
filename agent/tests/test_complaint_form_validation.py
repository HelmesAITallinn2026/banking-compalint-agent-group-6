from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_complaint_form_accepts_supported_mortgage_refusal_reason(monkeypatch):
    async def _create_complaint(*args, **kwargs):
        return "cmp1234567890abcd"

    monkeypatch.setattr("main.create_complaint", _create_complaint)
    monkeypatch.setattr("main.run_extraction_pipeline", lambda *_args, **_kwargs: None)

    response = client.post(
        "/complaint-form",
        data={
            "first_name": "Jane",
            "last_name": "Doe",
            "subject": "Mortgage rejection",
            "message": "The bank rejected my mortgage because of income.",
            "refusal_reason": "not_enough_income",
        },
    )

    assert response.status_code == 200


def test_complaint_form_rejects_unknown_refusal_reason():
    response = client.post(
        "/complaint-form",
        data={
            "first_name": "Jane",
            "last_name": "Doe",
            "subject": "Mortgage rejection",
            "message": "The bank rejected my mortgage.",
            "refusal_reason": "property_value_too_low",
        },
    )

    assert response.status_code == 422


def test_complaint_form_allows_empty_refusal_reason(monkeypatch):
    async def _create_complaint(*args, **kwargs):
        return "cmp1234567890abcd"

    monkeypatch.setattr("main.create_complaint", _create_complaint)
    monkeypatch.setattr("main.run_extraction_pipeline", lambda *_args, **_kwargs: None)

    response = client.post(
        "/complaint-form",
        data={
            "first_name": "Jane",
            "last_name": "Doe",
            "subject": "Card dispute",
            "message": "Charged twice.",
        },
    )

    assert response.status_code == 200
