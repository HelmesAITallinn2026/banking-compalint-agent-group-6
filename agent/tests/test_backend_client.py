import asyncio

import backend_client


def test_save_draft_response_uses_customer_subject(monkeypatch):
    captured = {}

    async def fake_get_complaint_by_id(complaint_id):
        return {"subject": "I have enough history"}

    def fake_agent_update(complaint_id, payload):
        captured["complaint_id"] = complaint_id
        captured["payload"] = payload

    monkeypatch.setattr(backend_client, "get_complaint_by_id", fake_get_complaint_by_id)
    monkeypatch.setattr(backend_client, "_agent_update", fake_agent_update)

    asyncio.run(backend_client.save_draft_response("123", "Hello there"))

    assert captured["complaint_id"] == "123"
    assert captured["payload"]["draftEmailSubject"] == "RE: I have enough history"
    assert captured["payload"]["draftEmailBody"] == "Hello there"


def test_save_draft_response_falls_back_when_subject_missing(monkeypatch):
    captured = {}

    async def fake_get_complaint_by_id(complaint_id):
        return {"subject": " "}

    def fake_agent_update(complaint_id, payload):
        captured["payload"] = payload

    monkeypatch.setattr(backend_client, "get_complaint_by_id", fake_get_complaint_by_id)
    monkeypatch.setattr(backend_client, "_agent_update", fake_agent_update)

    asyncio.run(backend_client.save_draft_response("123", "Hello there"))

    assert captured["payload"]["draftEmailSubject"] == "RE: Complaint"
