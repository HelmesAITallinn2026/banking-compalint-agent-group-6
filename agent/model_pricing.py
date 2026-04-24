from __future__ import annotations

import logging
import os

import httpx

from tracing import get_langfuse

logger = logging.getLogger(__name__)

# Env vars that hold OpenRouter model names — add new ones here as agents grow
MODEL_ENV_VARS = [
    "OCR_MODEL",
    "EXTRACTION_MODEL",
    "CATEGORIZATION_MODEL",
    "DATA_RETRIEVAL_MODEL",
    "DRAFTING_MODEL",
]

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


def _get_configured_models() -> list[str]:
    """Collect unique model names from env vars."""
    models: set[str] = set()
    for var in MODEL_ENV_VARS:
        val = os.getenv(var)
        if val:
            models.add(val)
    return list(models)


def _fetch_openrouter_pricing(model_ids: list[str]) -> dict[str, dict]:
    """Fetch pricing from OpenRouter's public API for the given model IDs.

    Returns {model_id: {"input": price_per_token, "output": price_per_token}}.
    """
    try:
        resp = httpx.get(OPENROUTER_MODELS_URL, timeout=10)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("Failed to fetch OpenRouter models: %s", exc)
        return {}

    data = resp.json().get("data", [])
    lookup = {m["id"]: m for m in data if "id" in m}

    result: dict[str, dict] = {}
    for model_id in model_ids:
        info = lookup.get(model_id)
        if not info:
            logger.warning("Model %s not found on OpenRouter", model_id)
            continue
        pricing = info.get("pricing", {})
        # OpenRouter prices are per-token strings
        try:
            result[model_id] = {
                "input": float(pricing.get("prompt", "0")),
                "output": float(pricing.get("completion", "0")),
            }
        except (ValueError, TypeError):
            logger.warning("Bad pricing data for %s: %s", model_id, pricing)
    return result


def _register_in_langfuse(model_id: str, input_price: float, output_price: float) -> None:
    """Register a custom model definition in Langfuse via REST API."""
    host = os.getenv("LANGFUSE_HOST", os.getenv("LANGFUSE_BASE_URL", "http://localhost:3000"))
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")

    if not public_key or not secret_key:
        return

    # Escape dots for regex match pattern
    escaped = model_id.replace(".", r"\.")
    match_pattern = f"(?i)^{escaped}$"

    payload = {
        "modelName": model_id,
        "matchPattern": match_pattern,
        "inputPrice": input_price,
        "outputPrice": output_price,
        "unit": "TOKENS",
    }

    try:
        resp = httpx.post(
            f"{host}/api/public/models",
            json=payload,
            auth=(public_key, secret_key),
            timeout=10,
        )
        if resp.status_code in (200, 201):
            logger.info("Registered model %s in Langfuse (input=%.10f, output=%.10f)", model_id, input_price, output_price)
        elif resp.status_code == 409:
            logger.info("Model %s already registered in Langfuse, skipping", model_id)
        else:
            logger.warning("Langfuse model registration for %s returned %s: %s", model_id, resp.status_code, resp.text[:200])
    except httpx.HTTPError as exc:
        logger.warning("Failed to register model %s in Langfuse: %s", model_id, exc)


def register_model_prices() -> None:
    """Fetch OpenRouter pricing and register models in Langfuse. Safe to call on every startup."""
    lf = get_langfuse()
    if not lf:
        logger.info("Langfuse disabled, skipping model price registration")
        return

    models = _get_configured_models()
    if not models:
        logger.info("No OpenRouter models configured, skipping price registration")
        return

    logger.info("Registering %d model(s) in Langfuse: %s", len(models), models)
    pricing = _fetch_openrouter_pricing(models)

    for model_id, prices in pricing.items():
        _register_in_langfuse(model_id, prices["input"], prices["output"])

    logger.info("Model price registration complete")
