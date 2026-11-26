"""Baseline generator: profile + request -> local LLM (Ollama) -> validated response.

The raw output is always returned, valid or not, so failures can be inspected and counted.
"""

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from pydantic import ValidationError

from schemas.llm_response import LLM_RESPONSE_ADAPTER, LLMResponse
from schemas.user_profile import SessionGenerationInput

from .prompt import render_system_prompt


class OllamaUnavailableError(RuntimeError):
    """Ollama could not be reached or returned an HTTP error."""


@dataclass(frozen=True)
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:7b"
    temperature: float = 0.0
    seed: int = 42
    timeout_seconds: float = 300.0
    # Constrained decoding with the response JSON schema. Part of the frozen configuration.
    use_json_schema: bool = True

    @classmethod
    def from_env(cls) -> "OllamaConfig":
        defaults = cls()
        return cls(
            base_url=os.getenv("OLLAMA_BASE_URL") or defaults.base_url,
            model=os.getenv("OLLAMA_MODEL") or defaults.model,
        )


@dataclass(frozen=True)
class GenerationResult:
    raw_output: str
    model: str
    latency_seconds: float
    response: LLMResponse | None
    validation_errors: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.response is not None


def build_user_message(session_input: SessionGenerationInput) -> str:
    """Serializes the input without internal identifiers or empty optional fields."""
    return session_input.model_dump_json(exclude_none=True, exclude={"user_profile": {"user_id"}})


def build_payload(session_input: SessionGenerationInput, config: OllamaConfig) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": render_system_prompt()},
            {"role": "user", "content": build_user_message(session_input)},
        ],
        "stream": False,
        "options": {"temperature": config.temperature, "seed": config.seed},
    }
    if config.use_json_schema:
        payload["format"] = LLM_RESPONSE_ADAPTER.json_schema()
    return payload


def _validation_errors(error: ValidationError, response_type: object) -> list[dict[str, Any]]:
    errors = []
    for item in error.errors():
        location = list(item["loc"])
        # In a discriminated union, Pydantic prefixes the location with the tag ("plan.plan...").
        if location and location[0] == response_type:
            location = location[1:]
        errors.append(
            {"location": ".".join(str(part) for part in location), "message": item["msg"]}
        )
    return errors


def _response_type(raw_output: str) -> object:
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        return None
    return parsed.get("response_type") if isinstance(parsed, dict) else None


def generate_session(
    session_input: SessionGenerationInput,
    config: OllamaConfig | None = None,
    client: httpx.Client | None = None,
) -> GenerationResult:
    config = config or OllamaConfig.from_env()
    http = client or httpx.Client(timeout=config.timeout_seconds)
    started = time.perf_counter()
    try:
        response = http.post(
            f"{config.base_url}/api/chat", json=build_payload(session_input, config)
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise OllamaUnavailableError(f"Ollama request failed: {error}") from error
    finally:
        if client is None:
            http.close()
    latency = time.perf_counter() - started

    raw_output = response.json().get("message", {}).get("content", "")
    try:
        parsed = LLM_RESPONSE_ADAPTER.validate_json(raw_output)
    except ValidationError as error:
        errors = _validation_errors(error, _response_type(raw_output))
        return GenerationResult(raw_output, config.model, latency, None, errors)
    return GenerationResult(raw_output, config.model, latency, parsed)
