# Langfuse Integration Design

## Problem

The agent pipeline (extraction → categorization → data retrieval → drafting) runs as async background tasks with no external observability. We have `agent_logs` in SQLite but can't inspect LLM call details (prompts, tokens, latency, cost), tool execution traces, or debug agent reasoning interactively. We need Langfuse integrated so every agent action is visible, searchable, and filterable by complaint.

## Approach

Use Langfuse v3 Python SDK with three integration layers:

1. **`@observe()` decorator** on pipeline functions → auto-creates traces/spans
2. **LangChain `CallbackHandler`** → auto-captures all LangChain agent LLM calls + tool calls
3. **Langfuse OpenAI wrapper** → auto-traces raw `openai.OpenAI()` calls in `ocr_document`

Each complaint pipeline run = 1 Langfuse trace, tagged with `complaint_id` as `session_id`.

## Self-Hosted Langfuse Setup

A `docker-compose.langfuse.yml` in the repo root:

- **Langfuse server** on `http://localhost:3000` (web UI + trace API)
- **PostgreSQL** (Langfuse internal metadata DB)
- **ClickHouse** (Langfuse analytics/trace storage)
- **Redis** (Langfuse cache)

After first launch, create a project in the Langfuse UI and copy API keys to `agent/.env`.

### Env vars (`agent/.env.example`)

```
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
```

## Python SDK Integration

### New dependency

Add `langfuse` to `agent/pyproject.toml`.

### New file: `agent/tracing.py`

Centralizes Langfuse setup:

```python
from __future__ import annotations

import os
from langfuse import Langfuse, observe, propagate_attributes
from langfuse.langchain import CallbackHandler

# Re-export for convenience
__all__ = ["observe", "propagate_attributes", "get_langfuse", "get_langfuse_handler", "flush"]

_langfuse: Langfuse | None = None

def _is_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY"))

def get_langfuse() -> Langfuse | None:
    global _langfuse
    if not _is_enabled():
        return None
    if _langfuse is None:
        _langfuse = Langfuse()
    return _langfuse

def get_langfuse_handler(complaint_id: str) -> CallbackHandler | None:
    if not _is_enabled():
        return None
    return CallbackHandler(
        session_id=complaint_id,
        tags=["hackathon", "banking-complaint"],
    )

def flush():
    lf = get_langfuse()
    if lf:
        lf.flush()
```

### Changes to `agent/extracting_agent/agent.py`

1. Replace `import openai` with `from langfuse.openai import openai` — drop-in replacement that auto-traces all raw OpenAI calls (OCR vision calls)
2. In `run_extraction_agent()`:
   - Wrap with `@observe(name="extraction-agent")`
   - Use `propagate_attributes(session_id=complaint_id, trace_name="extraction-pipeline", tags=["hackathon", "banking-complaint"])`
   - Get `CallbackHandler` from `tracing.py` and pass to `agent.invoke(config={"callbacks": [handler]})`
3. Pass `langfuse_observation_id` metadata on raw OpenAI calls so they nest under the correct trace

### Changes to `agent/pipeline.py`

1. Wrap `run_extraction_pipeline()` with `@observe(name="extraction-pipeline")`
2. Wrap `run_drafting_pipeline()` with `@observe(name="drafting-pipeline")`
3. Use `propagate_attributes(session_id=complaint_id)` at the top of each pipeline function
4. Call `flush()` at the end of each pipeline to ensure traces are sent before background task exits

## Trace Structure

Each complaint produces traces like:

```
Trace: "extraction-pipeline" (session_id=complaint_id)
├── Span: run_extraction_agent
│   ├── Generation: LLM call (ChatOpenAI → extraction model)
│   ├── Span: tool:analyze_document_type
│   ├── Generation: LLM call (tool routing decision)
│   ├── Span: tool:ocr_document
│   │   └── Generation: OpenAI vision call (auto-traced via wrapper)
│   ├── Span: tool:extract_data
│   │   └── Generation: LLM structured output call
│   └── Span: tool:save_complaint_data
├── Span: categorization_agent (placeholder)
└── Span: data_retrieval_agent (placeholder)

Trace: "drafting-pipeline" (session_id=complaint_id)
└── Span: message_drafting_agent (placeholder)
```

## Error Handling

- Langfuse SDK is non-blocking — if Langfuse is down, pipeline still works (traces silently dropped)
- `flush()` called at end of each pipeline
- No retry logic (hackathon scope)
- If `LANGFUSE_PUBLIC_KEY` is not set, `tracing.py` returns `None` handlers — all tracing is disabled gracefully

## Files Changed

| File | Change |
|------|--------|
| `docker-compose.langfuse.yml` (new) | Self-hosted Langfuse stack |
| `agent/pyproject.toml` | Add `langfuse` dependency |
| `agent/.env.example` | Add Langfuse env vars |
| `agent/tracing.py` (new) | Centralized Langfuse setup |
| `agent/extracting_agent/agent.py` | OpenAI wrapper import, @observe, CallbackHandler |
| `agent/pipeline.py` | @observe decorators, propagate_attributes, flush |
