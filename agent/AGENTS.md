# Agent Module – Banking Complaint Processing System

## Overview

This module implements an AI-powered multi-agent system for automated processing of consumer banking complaints. The system uses a linear pipeline of four specialized agents that extract data, categorize complaints, retrieve supporting information, and draft customer responses.

## Coding standard and general approach
- This is hackathon project
- Simple is better than complex
- We want to have demo to showcase how it's working, not a production ready app
- 

**Tech stack:** Python, FastAPI, LangChain, LangGraph, Langfuse

## Architecture

```
Customer Complaint (form + files)
        │
        ▼
┌─────────────────┐
│ Extraction Agent │ ── analyzes documents, extracts structured data
└────────┬────────┘
         │ (if data incomplete → Drafting Agent for rejection)
         ▼
┌──────────────────────┐
│ Categorization Agent │ ── assigns complaint category using complaint tree
└────────┬─────────────┘
         ▼
┌───────────────────────┐
│ Data Retrieval Agent  │ ── fetches internal banking data, gives recommendation
└────────┬──────────────┘
         │
         ▼
   [Human Review] ── approves/rejects recommendation
         │
         ▼
┌──────────────────────┐
│ Message Drafting Agent│ ── drafts formal response letter
└────────┬─────────────┘
         ▼
   [Human Review] ── verifies draft, sends to customer
```

## API Endpoints

- **POST /complaint-form** – Receives complaint submission
  - Body: `first_name`, `last_name`, `subject`, `message`, `refusal_reason`, `files`
  - Triggers the full agent pipeline starting with Extraction Agent

- **POST /draft-response** – Triggers response drafting
  - Body: `first_name`, `last_name`, `decision`, `refusal_reason`, `clarification_message`
  - Used after human review to generate the final customer response

## Agents

### 1. Extraction Agent

First agent in the pipeline. Processes raw complaint data and attached files.

**Responsibilities:**
- Classify document type (structured text vs scanned image)
- Read document content directly or via OCR
- Extract structured data from documents
- Validate data relevance and completeness
- Route to Drafting Agent if documents are insufficient

**Tools:**
- `analyze_document_type` – Determines if document can be read directly or needs OCR
- `ocr_document` – Converts image/scanned documents to text via OCR
- `extract_data` – Extracts structured output based on document type
- `save_complaint_data` – Persists extracted data to DB via backend

**LLM notes:** Can use multimodal LLM with vision capabilities as an alternative to OCR.

### 2. Categorization Agent

Assigns the correct complaint category using an externally maintained complaint tree.

**Responsibilities:**
- Load complaint tree into context (LLM-optimized format)
- Categorize the complaint ticket
- Save categorization for human verification

**Tools:**
- `load_complaint_tree` – Loads/formats complaint tree from DB into context
- `save_categorization` – Persists category assignment

**Design note:** Simplest agent in the pipeline. Could be implemented as a single tool rather than a standalone agent if complexity stays low.

### 3. Data Retrieval Agent

Fetches all internal banking data needed to resolve the complaint and provides a recommendation.

**Responsibilities:**
- Determine what data is required based on complaint category and client info
- Retrieve data from internal banking systems
- Generate POSITIVE or NEGATIVE recommendation with reasoning
- Log every data access operation with justification

**Tools:**
- Tools connecting to internal banking system APIs (account data, transaction history, etc.)
- `save_recommendation` – Persists recommendation to DB

**LLM notes:** Decision-making rules should be loaded from an external source (prompt or DB) to keep them current. Every banking API call must be documented with the reason for the request.

### 4. Message Drafting Agent

Generates formal customer response letters.

**Responsibilities:**
- Draft response based on recommendation and customer data
- Handle multiple trigger scenarios:
  - End of pipeline (recommendation ready)
  - Early exit (incomplete/invalid documents from Extraction Agent)
  - Process failures requiring customer contact
- Save draft in review-ready state

**Inputs considered:**
- Data completeness status
- Process success/failure status
- Recommendation (positive/negative) with reasoning

**Design note:** For simple cases, can be a single LLM tool call rather than a full agent.

## Coding Conventions

- Use **LangGraph** for agent orchestration and state management
- Use **LangChain** for tools, retrievers, structured output, and document loaders
- Use **Langfuse** for tracing, evaluation, prompt management, and cost monitoring
- Use **FastAPI** for the HTTP API layer
- All agents must produce structured, auditable log entries containing:
  - Timestamp, agent identity, action type
  - Input context, reasoning process, output
  - Human verification events
- Store persistent data in **SQLite** via the backend API
- Don't focus on patterns and clean code prinicples

## LLM Configuration

- **Enterprise providers:** OpenRouter

## Observability

- **Langfuse** – Real-time tracing dashboard for agent runs, token usage, errors
- **Structured DB logging** – Persistent audit trail in defined schema for compliance
- **Alerting** – Monitor for categorization drift, latency spikes, high override rates, error rate anomalies

