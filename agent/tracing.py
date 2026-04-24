from __future__ import annotations

import os

from langfuse import Langfuse, observe, propagate_attributes
from langfuse.langchain import CallbackHandler

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
    """Create a Langfuse callback handler and tag the trace with complaint metadata."""
    if not _is_enabled():
        return None
    handler = CallbackHandler()
    # After the handler creates its trace, update it with session/tag info
    lf = get_langfuse()
    if lf:
        lf.update_current_trace(
            session_id=complaint_id,
            tags=["hackathon", "banking-complaint"],
        )
    return handler


def flush() -> None:
    lf = get_langfuse()
    if lf:
        lf.flush()
