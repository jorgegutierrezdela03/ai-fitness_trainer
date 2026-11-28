"""Local Ollama-based qualitative evaluation for validated training plans."""

import json
import os
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from baseline.generator import OllamaUnavailableError, build_user_message
from schemas.training_plan import TrainingPlanLLM
from schemas.user_profile import SessionGenerationInput

JUDGE_SYSTEM_PROMPT_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "judge_system_prompt.md"
)


def render_judge_system_prompt() -> str:
    return JUDGE_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


class StrictJudgeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CriterionScore(StrictJudgeModel):
    reasoning: str = Field(..., min_length=1)
    score: int = Field(..., ge=0, le=5)


class JudgeEvaluation(StrictJudgeModel):
    profile_alignment: CriterionScore
    request_adherence: CriterionScore
    programming_quality: CriterionScore
    safety_and_compatibility: CriterionScore
    overall_summary: str = Field(..., min_length=1)
    critical_flags: list[str]


@dataclass(frozen=True)
class JudgeConfig:
    base_url: str = "http://localhost:11434"
    model: str = "gemma4"
    temperature: float = 0.0
    seed: int = 42
    timeout_seconds: float = 120.0

    @classmethod
    def from_env(cls) -> "JudgeConfig":
        defaults = cls()
        return cls(
            base_url=os.getenv("OLLAMA_BASE_URL") or defaults.base_url,
            model=os.getenv("JUDGE_MODEL") or defaults.model,
        )


@dataclass(frozen=True)
class JudgeResult:
    is_valid: bool
    judgment: JudgeEvaluation | None
    raw_output: str
    validation_errors: list[dict[str, str]]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class JudgeSummary:
    total_evaluated: int
    valid_rate: float | None
    profile_alignment_mean: float | None
    request_adherence_mean: float | None
    programming_quality_mean: float | None
    safety_and_compatibility_mean: float | None


def build_judge_payload(
    session_input: SessionGenerationInput,
    plan: TrainingPlanLLM,
    config: JudgeConfig,
) -> dict[str, Any]:
    user_content = json.dumps(
        {
            "session_input": json.loads(build_user_message(session_input)),
            "training_plan": plan.model_dump(mode="json", exclude_none=True),
        },
        ensure_ascii=False,
    )
    return {
        "model": config.model,
        "messages": [
            {"role": "system", "content": render_judge_system_prompt()},
            {"role": "user", "content": user_content},
        ],
        "stream": False,
        "options": {"temperature": config.temperature, "seed": config.seed},
        "format": JudgeEvaluation.model_json_schema(),
    }


def _validation_errors(error: ValidationError) -> list[dict[str, str]]:
    return [
        {
            "location": ".".join(str(part) for part in item["loc"]),
            "message": item["msg"],
        }
        for item in error.errors()
    ]


def judge_plan(
    session_input: SessionGenerationInput,
    plan: TrainingPlanLLM,
    config: JudgeConfig | None = None,
    client: httpx.Client | None = None,
) -> JudgeResult:
    config = config or JudgeConfig.from_env()
    http = client or httpx.Client(timeout=config.timeout_seconds)
    started = time.perf_counter()
    try:
        response = http.post(
            f"{config.base_url}/api/chat",
            json=build_judge_payload(session_input, plan, config),
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise OllamaUnavailableError(f"Ollama judge request failed: {error}") from error
    finally:
        if client is None:
            http.close()
    latency_ms = (time.perf_counter() - started) * 1000

    raw_output = response.json().get("message", {}).get("content", "")
    try:
        judgment = JudgeEvaluation.model_validate_json(raw_output)
    except ValidationError as error:
        return JudgeResult(
            is_valid=False,
            judgment=None,
            raw_output=raw_output,
            validation_errors=_validation_errors(error),
            metadata={"model": config.model, "latency_ms": round(latency_ms, 2)},
        )
    return JudgeResult(
        is_valid=True,
        judgment=judgment,
        raw_output=raw_output,
        validation_errors=[],
        metadata={"model": config.model, "latency_ms": round(latency_ms, 2)},
    )


def summarize_judgments(results: Sequence[JudgeResult]) -> JudgeSummary:
    valid = [result.judgment for result in results if result.is_valid and result.judgment]

    def mean_score(criterion: str) -> float | None:
        if not valid:
            return None
        return sum(getattr(judgment, criterion).score for judgment in valid) / len(valid)

    return JudgeSummary(
        total_evaluated=len(results),
        valid_rate=len(valid) / len(results) if results else None,
        profile_alignment_mean=mean_score("profile_alignment"),
        request_adherence_mean=mean_score("request_adherence"),
        programming_quality_mean=mean_score("programming_quality"),
        safety_and_compatibility_mean=mean_score("safety_and_compatibility"),
    )
