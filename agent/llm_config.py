from __future__ import annotations

import os

from langchain_openai import ChatOpenAI
from langfuse.openai import openai


def get_required_envs(*names: str) -> dict[str, str]:
    values: dict[str, str] = {}
    missing: list[str] = []
    for name in names:
        value = os.getenv(name)
        if value:
            values[name] = value
        else:
            missing.append(name)

    if missing:
        missing_list = ", ".join(missing)
        raise RuntimeError(f"Missing required LLM environment variables: {missing_list}")

    return values


def get_required_env(name: str) -> str:
    return get_required_envs(name)[name]


def build_openrouter_chat_model(
    *,
    model_env_var: str,
    temperature: float,
    model_name: str | None = None,
) -> ChatOpenAI:
    required_names = ["OPENROUTER_API_KEY", "OPENROUTER_BASE_URL"]
    if model_name is None:
        required_names.insert(0, model_env_var)
    config = get_required_envs(*required_names)
    model = model_name or config[model_env_var]
    return ChatOpenAI(
        model=model,
        api_key=config["OPENROUTER_API_KEY"],
        base_url=config["OPENROUTER_BASE_URL"],
        temperature=temperature,
        extra_body={"usage": {"include": True}},
    )


def build_openrouter_client() -> openai.OpenAI:
    config = get_required_envs("OPENROUTER_API_KEY", "OPENROUTER_BASE_URL")
    return openai.OpenAI(
        api_key=config["OPENROUTER_API_KEY"],
        base_url=config["OPENROUTER_BASE_URL"],
    )
