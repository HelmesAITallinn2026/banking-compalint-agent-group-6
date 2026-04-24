from database import create_agent_log, save_draft_response, save_recommendation, update_complaint_status
from extracting_agent import run_extraction_agent
from schemas import ComplaintStatus
from tracing import flush, observe, propagate_attributes


@observe(name="extraction-pipeline")
async def run_extraction_pipeline(complaint_id):
    """Run extraction agent, then placeholder categorization + recommendation."""
    with propagate_attributes(session_id=complaint_id, tags=["hackathon", "banking-complaint"]):
        await run_extraction_agent(complaint_id)

        # Placeholder: categorization agent (to be implemented separately)
        await update_complaint_status(complaint_id, ComplaintStatus.categorised)
        await create_agent_log(complaint_id, "categorization_agent", "categorize",
            {"complaint_id": complaint_id}, "Assigned placeholder category.",
            {"category": "general_banking_complaint", "status": ComplaintStatus.categorised})

        # Placeholder: data retrieval agent (to be implemented separately)
        await create_agent_log(complaint_id, "data_retrieval_agent", "recommendation",
            {"complaint_id": complaint_id}, "Used demo decision rules.",
            {"recommendation": "POSITIVE", "reasoning": "Ready for human review."})

        await save_recommendation(complaint_id, "general_banking_complaint", "POSITIVE", "Ready for human review.")
    flush()


@observe(name="drafting-pipeline")
async def run_drafting_pipeline(complaint_id, decision, refusal_reason=None, clarification_message=None):
    """Placeholder pipeline: draft a response letter."""
    with propagate_attributes(session_id=complaint_id, tags=["hackathon", "banking-complaint"]):
        await update_complaint_status(complaint_id, ComplaintStatus.draft_created)
        draft = (
            f"Dear customer,\n\n"
            f"We reviewed your complaint and the decision is {decision}.\n\n"
            f"Refusal reason: {refusal_reason or 'N/A'}\n"
            f"Clarification: {clarification_message or 'N/A'}\n\n"
            f"Kind regards,\nBank Complaint Team"
        )
        await create_agent_log(complaint_id, "message_drafting_agent", "draft_response",
            {"decision": decision, "refusal_reason": refusal_reason, "clarification_message": clarification_message},
            "Built placeholder response.", {"draft_response": draft, "status": ComplaintStatus.draft_created})
        await save_draft_response(complaint_id, draft)
    flush()
