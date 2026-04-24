import json
import logging

from categorization_agent import run_categorization_agent
from data_retrieval_agent import run_data_retrieval_agent
from database import get_complaint_by_id, update_complaint_status
from drafting_agent import run_drafting_agent
from extracting_agent import run_extraction_agent
from mortgage_rules import should_early_reject_mortgage_case
from schemas import ComplaintStatus
from tracing import flush, observe, propagate_attributes

logger = logging.getLogger(__name__)


@observe(name="extraction-pipeline")
async def run_extraction_pipeline(complaint_id):
    """Run full pipeline: extraction → categorization → data retrieval → recommendation_ready."""
    with propagate_attributes(session_id=complaint_id, tags=["hackathon", "banking-complaint"]):
        # Step 1: Extraction
        await run_extraction_agent(complaint_id)

        # Check if extracted data is relevant — early exit if not
        complaint = await get_complaint_by_id(complaint_id)
        extracted_raw = complaint.get("extracted_data") if complaint else None
        if extracted_raw:
            try:
                extracted = json.loads(extracted_raw) if isinstance(extracted_raw, str) else extracted_raw

                # Mortgage-documents early rejection
                if should_early_reject_mortgage_case(
                    refusal_reason=complaint.get("refusal_reason"),
                    extracted_data=extracted,
                ):
                    logger.info("Complaint %s: mortgage documents incomplete, early exit to drafting", complaint_id)
                    await run_drafting_agent(
                        complaint_id,
                        "NEGATIVE",
                        "wrong_or_incomplete_documents",
                        "Submitted mortgage documents were missing or incomplete.",
                    )
                    flush()
                    return

                # Generic irrelevance check
                if not extracted.get("is_relevant", True):
                    logger.info("Complaint %s: data not relevant, early exit to drafting", complaint_id)
                    await run_drafting_agent(complaint_id, "NEGATIVE", "insufficient_documents",
                                            "Submitted documents were not relevant or incomplete.")
                    flush()
                    return
            except (json.JSONDecodeError, AttributeError):
                pass

        # Step 2: Categorization
        await run_categorization_agent(complaint_id)

        # Step 3: Data Retrieval + Recommendation
        await run_data_retrieval_agent(complaint_id)

        # Pipeline stops here — status is recommendation_ready, waiting for human review
    flush()


@observe(name="drafting-pipeline")
async def run_drafting_pipeline(complaint_id, decision, refusal_reason=None, clarification_message=None):
    """Run the drafting agent to generate a formal response letter."""
    with propagate_attributes(session_id=complaint_id, tags=["hackathon", "banking-complaint"]):
        await run_drafting_agent(complaint_id, decision, refusal_reason, clarification_message)
    flush()
