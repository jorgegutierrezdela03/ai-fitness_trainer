import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from baseline.generator import OllamaUnavailableError
from evaluation.judge import (
    CriterionScore,
    JudgeConfig,
    JudgeEvaluation,
    JudgeResult,
    build_judge_payload,
    judge_plan,
    render_judge_system_prompt,
    summarize_judgments,
)
from schemas.training_plan import TrainingPlanLLM
from schemas.user_profile import SessionGenerationInput

EXAMPLES = Path(__file__).resolve().parents[1] / "data" / "evaluation" / "examples"
BACKEND_FIELDS = ("session_id", "user_id", "generated_at", "exercise_ids_resolved")


@pytest.fixture
def session_input():
    data = json.loads((EXAMPLES / "sample_user_input.json").read_text(encoding="utf-8"))
    return SessionGenerationInput.model_validate(data)


@pytest.fixture
def plan():
    data = json.loads(
        (EXAMPLES / "training_plan_schema_validation.json").read_text(encoding="utf-8")
    )
    llm_data = {key: value for key, value in data.items() if key not in BACKEND_FIELDS}
    return TrainingPlanLLM.model_validate(llm_data)


def judgment_data(scores=None):
    scores = {
        "profile_alignment": 4,
        "request_adherence": 3,
        "programming_quality": 5,
        "safety_and_compatibility": 4,
        **(scores or {}),
    }
    return {
        **{
            criterion: {"reasoning": f"Concrete reasoning for {criterion}.", "score": score}
            for criterion, score in scores.items()
        },
        "overall_summary": "The plan is appropriate, with a few areas for improvement.",
        "critical_flags": [],
    }


def ollama_client(content: str, status: int = 200) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        return httpx.Response(status, json={"message": {"content": content}})

    return httpx.Client(transport=httpx.MockTransport(handler))


def make_valid_result(scores) -> JudgeResult:
    data = judgment_data(scores)
    judgment = JudgeEvaluation.model_validate(data)
    return JudgeResult(
        is_valid=True,
        judgment=judgment,
        raw_output=json.dumps(data),
        validation_errors=[],
        metadata={"model": "gemma4", "latency_ms": 10.0},
    )


def test_build_judge_payload_excludes_user_id_and_uses_structured_output(
    session_input, plan
):
    config = JudgeConfig()
    payload = build_judge_payload(session_input, plan, config)
    user_message = json.loads(payload["messages"][1]["content"])
    criterion_properties = payload["format"]["$defs"]["CriterionScore"]["properties"]
    system_prompt = " ".join(payload["messages"][0]["content"].split())

    assert payload["model"] == "gemma4"
    assert payload["messages"][0]["content"] == render_judge_system_prompt()
    assert "You are an expert auditor" in payload["messages"][0]["content"]
    assert "Write all free-text fields in English." in system_prompt
    assert "USR-001" not in payload["messages"][1]["content"]
    assert "user_id" not in user_message["session_input"]["user_profile"]
    assert "training_plan" in user_message
    assert payload["format"] == JudgeEvaluation.model_json_schema()
    assert list(criterion_properties) == ["reasoning", "score"]
    assert criterion_properties["score"]["minimum"] == 0
    assert criterion_properties["score"]["maximum"] == 5
    assert payload["options"] == {"temperature": 0.0, "seed": 42}
    assert payload["stream"] is False


def test_judge_config_reads_model_and_shared_ollama_url(monkeypatch):
    monkeypatch.setenv("JUDGE_MODEL", "gpt-oss")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11435")

    config = JudgeConfig.from_env()

    assert config.model == "gpt-oss"
    assert config.base_url == "http://localhost:11435"
    assert config.timeout_seconds == 120.0


def test_valid_judgment_is_parsed(session_input, plan):
    raw = json.dumps(judgment_data())
    with ollama_client(raw) as client:
        result = judge_plan(session_input, plan, JudgeConfig(), client)

    assert result.is_valid
    assert isinstance(result.judgment, JudgeEvaluation)
    assert result.judgment.profile_alignment.score == 4
    assert result.raw_output == raw
    assert result.validation_errors == []
    assert result.metadata["model"] == "gemma4"
    assert result.metadata["latency_ms"] >= 0


@pytest.mark.parametrize(
    "raw",
    [
        json.dumps(judgment_data({"profile_alignment": 6})),
        "esto no es JSON",
    ],
)
def test_invalid_judgment_preserves_raw_output_and_errors(session_input, plan, raw):
    with ollama_client(raw) as client:
        result = judge_plan(session_input, plan, JudgeConfig(), client)

    assert not result.is_valid
    assert result.judgment is None
    assert result.raw_output == raw
    assert result.validation_errors
    assert all(
        isinstance(error["location"], str) and isinstance(error["message"], str)
        for error in result.validation_errors
    )


def test_judge_propagates_ollama_http_errors(session_input, plan):
    with ollama_client("", status=500) as client, pytest.raises(OllamaUnavailableError):
        judge_plan(session_input, plan, JudgeConfig(), client)


def test_summarize_judgments_ignores_invalid_scores_but_counts_invalid_results():
    first = make_valid_result(
        {
            "profile_alignment": 0,
            "request_adherence": 5,
            "programming_quality": 2,
            "safety_and_compatibility": 4,
        }
    )
    second = make_valid_result(
        {
            "profile_alignment": 4,
            "request_adherence": 3,
            "programming_quality": 4,
            "safety_and_compatibility": 2,
        }
    )
    invalid = JudgeResult(
        is_valid=False,
        judgment=None,
        raw_output="invalid",
        validation_errors=[{"location": "", "message": "Invalid JSON"}],
        metadata={"model": "gemma4", "latency_ms": 5.0},
    )

    summary = summarize_judgments([first, invalid, second])

    assert summary.total_evaluated == 3
    assert summary.valid_rate == pytest.approx(2 / 3)
    assert summary.profile_alignment_mean == pytest.approx(2)
    assert summary.request_adherence_mean == pytest.approx(4)
    assert summary.programming_quality_mean == pytest.approx(3)
    assert summary.safety_and_compatibility_mean == pytest.approx(3)


def test_summarize_judgments_returns_none_for_empty_or_all_invalid_results():
    invalid = JudgeResult(
        is_valid=False,
        judgment=None,
        raw_output="invalid",
        validation_errors=[],
        metadata={},
    )

    for results in ([], [invalid]):
        summary = summarize_judgments(results)
        assert summary.total_evaluated == len(results)
        if results:
            assert summary.valid_rate == 0
        else:
            assert summary.valid_rate is None
        assert summary.profile_alignment_mean is None
        assert summary.request_adherence_mean is None
        assert summary.programming_quality_mean is None
        assert summary.safety_and_compatibility_mean is None


def test_criterion_score_requires_reasoning_before_bounded_score():
    assert list(CriterionScore.model_fields) == ["reasoning", "score"]
    assert CriterionScore(reasoning="No material issue.", score=0).score == 0
    with pytest.raises(ValidationError):
        CriterionScore(reasoning="Invalid low score.", score=-1)
    with pytest.raises(ValidationError):
        CriterionScore(reasoning="Invalid high score.", score=6)
