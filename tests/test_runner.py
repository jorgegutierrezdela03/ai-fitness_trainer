import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import evaluation.runner as runner
from baseline.generator import OllamaUnavailableError
from evaluation.judge import JudgeConfig, JudgeEvaluation, JudgeResult
from schemas.training_plan import TrainingPlanLLM
from schemas.user_profile import SessionGenerationInput

EXAMPLES = Path(__file__).resolve().parents[1] / "data" / "evaluation" / "examples"
BACKEND_FIELDS = ("session_id", "user_id", "generated_at", "exercise_ids_resolved")


@pytest.fixture
def sample_input():
    return json.loads((EXAMPLES / "sample_user_input.json").read_text(encoding="utf-8"))


@pytest.fixture
def valid_plan():
    data = json.loads(
        (EXAMPLES / "training_plan_schema_validation.json").read_text(encoding="utf-8")
    )
    llm_data = {key: value for key, value in data.items() if key not in BACKEND_FIELDS}
    return TrainingPlanLLM.model_validate(llm_data)


def write_dataset(path, sample_input, case_ids):
    rows = []
    for case_id in case_ids:
        row = json.loads(json.dumps(sample_input))
        row["user_profile"]["user_id"] = case_id
        rows.append(row)
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return rows


def valid_judge_result():
    data = {
        "profile_alignment": {"reasoning": "The plan fits the profile.", "score": 4},
        "request_adherence": {"reasoning": "It follows the request.", "score": 5},
        "programming_quality": {"reasoning": "The session is balanced.", "score": 3},
        "safety_and_compatibility": {"reasoning": "No major risk is apparent.", "score": 4},
        "overall_summary": "The plan is suitable with minor improvements.",
        "critical_flags": [],
    }
    return JudgeResult(
        is_valid=True,
        judgment=JudgeEvaluation.model_validate(data),
        raw_output=json.dumps(data),
        validation_errors=[],
        metadata={"model": "judge-test", "latency_ms": 1.0},
    )


def generation_record(case_id, session_input, raw_output, category=None):
    input_data = json.loads(json.dumps(session_input))
    input_data["user_profile"]["user_id"] = case_id
    parsed_input = SessionGenerationInput.model_validate(input_data)
    return {
        "case_id": case_id,
        "category": category or runner._category_for_case(case_id),
        "session_input": parsed_input.model_dump(mode="json", exclude_none=True),
        "raw_output": raw_output,
        "is_valid": True,
        "validation_errors": [],
        "metadata": {"model": "generator-test", "latency_seconds": 0.1},
        "error": None,
    }


def write_generations(run_dir, records):
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "generations.jsonl"
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    return path


def test_generate_writes_config_limited_outputs_and_continues_after_failure(
    tmp_path, sample_input, monkeypatch
):
    dataset = tmp_path / "dataset.json"
    write_dataset(dataset, sample_input, ["GD-STD-01", "GD-SAF-02", "GD-OOS-03"])
    calls = []

    def fake_generate(session_input, config):
        case_id = session_input.user_profile.user_id
        calls.append(case_id)
        if case_id == "GD-SAF-02":
            raise OllamaUnavailableError("Ollama is unavailable")
        return SimpleNamespace(
            raw_output='{"response_type":"out_of_scope","message":"No."}',
            is_valid=True,
            validation_errors=[],
            model=config.model,
            latency_seconds=0.25,
        )

    monkeypatch.setattr(runner, "generate_session", fake_generate)
    run_dir = runner.generate_run(
        dataset=dataset,
        runs_dir=tmp_path / "runs",
        run_id="beta-run",
        model="generator-test",
        limit=2,
    )

    records = runner._read_jsonl(run_dir / "generations.jsonl")
    config = json.loads((run_dir / "run_config.json").read_text(encoding="utf-8"))

    assert calls == ["GD-STD-01", "GD-SAF-02"]
    assert len(records) == 2
    assert records[0]["category"] == "STD"
    assert records[0]["error"] is None
    assert records[0]["metadata"]["latency_seconds"] == 0.25
    assert records[1]["category"] == "SAF"
    assert records[1]["raw_output"] == ""
    assert records[1]["error"] == "Ollama is unavailable"
    assert config["model"] == "generator-test"
    assert config["temperature"] == 0.0
    assert config["seed"] == 42
    assert config["dataset"] == str(dataset.resolve())
    assert config["created_at"]


def test_generate_resume_skips_previously_saved_case_ids(tmp_path, sample_input, monkeypatch):
    dataset = tmp_path / "dataset.json"
    write_dataset(dataset, sample_input, ["GD-STD-01", "GD-CMP-02", "GD-AMB-03"])
    calls = []

    def fake_generate(session_input, config):
        calls.append(session_input.user_profile.user_id)
        return SimpleNamespace(
            raw_output="{}",
            is_valid=False,
            validation_errors=[],
            model=config.model,
            latency_seconds=0.1,
        )

    monkeypatch.setattr(runner, "generate_session", fake_generate)
    run_dir = runner.generate_run(
        dataset=dataset,
        runs_dir=tmp_path / "runs",
        run_id="resume-run",
        model="generator-test",
        limit=1,
    )
    runner.generate_run(
        dataset=dataset,
        runs_dir=tmp_path / "runs",
        run_id="resume-run",
        model="generator-test",
        resume=True,
    )

    assert calls == ["GD-STD-01", "GD-CMP-02", "GD-AMB-03"]
    assert len(runner._read_jsonl(run_dir / "generations.jsonl")) == 3


def test_generate_requires_run_id_when_resuming(tmp_path, sample_input):
    dataset = tmp_path / "dataset.json"
    write_dataset(dataset, sample_input, ["GD-STD-01"])

    with pytest.raises(ValueError, match="requires --run-id"):
        runner.generate_run(dataset=dataset, runs_dir=tmp_path / "runs", resume=True)


def test_evaluate_runs_metrics_for_all_and_judge_only_for_valid_plans(
    tmp_path, sample_input, valid_plan, monkeypatch
):
    plan_output = json.dumps(
        {"response_type": "plan", "plan": valid_plan.model_dump(mode="json", exclude_none=True)}
    )
    generations = [
        generation_record("GD-STD-01", sample_input, plan_output),
        generation_record(
            "GD-CMP-01",
            sample_input,
            json.dumps({"response_type": "plan", "plan": {"title": "Incomplete"}}),
        ),
        generation_record(
            "GD-AMB-01",
            sample_input,
            json.dumps({"response_type": "clarification", "questions": ["Which day?"]}),
        ),
        generation_record(
            "GD-SAF-01",
            sample_input,
            json.dumps(
                {
                    "response_type": "safety_referral",
                    "reason": "warning_sign",
                    "message": "Consult a professional.",
                }
            ),
        ),
        generation_record(
            "GD-OOS-01",
            sample_input,
            json.dumps({"response_type": "out_of_scope", "message": "Out of scope."}),
        ),
        generation_record("GD-STD-02", sample_input, "not JSON"),
    ]
    run_dir = tmp_path / "run"
    write_generations(run_dir, generations)
    real_evaluate_output = runner.evaluate_output
    metric_calls = []
    judge_calls = []

    def spy_evaluate_output(raw_output, **kwargs):
        metric_calls.append(raw_output)
        return real_evaluate_output(raw_output, **kwargs)

    def fake_judge(session_input, plan, config):
        assert isinstance(config, JudgeConfig)
        judge_calls.append((session_input, plan))
        return valid_judge_result()

    monkeypatch.setattr(runner, "evaluate_output", spy_evaluate_output)
    monkeypatch.setattr(runner, "judge_plan", fake_judge)
    summary = runner.evaluate_run(run_dir)

    evaluations = runner._read_jsonl(run_dir / "evaluations.jsonl")
    written_summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert len(metric_calls) == len(generations)
    assert len(judge_calls) == 1
    assert len(evaluations) == len(generations)
    assert evaluations[0]["judge"]["judgment"]["profile_alignment"]["score"] == 4
    assert all(record["judge"] is None for record in evaluations[1:])
    assert summary == written_summary
    assert summary["deterministic_summary"]["total"] == 6
    assert summary["deterministic_summary"]["schema_valid_rate"] == pytest.approx(4 / 6)
    assert summary["judge_summary"]["total_evaluated"] == 1
    assert summary["judge_summary"]["valid_rate"] == 1
    assert set(summary["by_category"]) == {"STD", "CMP", "AMB", "SAF", "OOS"}
    assert summary["by_category"]["STD"]["deterministic_summary"]["total"] == 2
    assert summary["by_category"]["STD"]["judge_summary"]["total_evaluated"] == 1


def test_evaluate_skip_judge_and_judge_errors_are_recorded_and_summarized(
    tmp_path, sample_input, valid_plan, monkeypatch
):
    plan_output = json.dumps(
        {"response_type": "plan", "plan": valid_plan.model_dump(mode="json", exclude_none=True)}
    )
    generations = [
        generation_record("GD-STD-01", sample_input, plan_output),
        generation_record(
            "GD-OOS-01",
            sample_input,
            json.dumps({"response_type": "out_of_scope", "message": "Out of scope."}),
        ),
    ]
    skip_dir = tmp_path / "skip"
    write_generations(skip_dir, generations)

    def should_not_judge(session_input, plan, config):
        assert session_input is not None
        assert plan is not None
        assert config is not None
        raise AssertionError("Judge should be skipped")

    monkeypatch.setattr(runner, "judge_plan", should_not_judge)
    skipped = runner.evaluate_run(skip_dir, skip_judge=True)
    assert skipped["judge_summary"] is None
    skip_records = runner._read_jsonl(skip_dir / "evaluations.jsonl")
    assert all(record["judge"] is None for record in skip_records)

    error_dir = tmp_path / "judge-error"
    write_generations(error_dir, generations)

    def failing_judge(session_input, plan, config):
        assert session_input is not None
        assert isinstance(plan, TrainingPlanLLM)
        raise OllamaUnavailableError(f"Judge Ollama unavailable ({config.model})")

    monkeypatch.setattr(runner, "judge_plan", failing_judge)
    summary = runner.evaluate_run(error_dir)
    records = runner._read_jsonl(error_dir / "evaluations.jsonl")

    assert records[0]["judge"] is None
    assert records[0]["judge_error"].startswith("Judge Ollama unavailable")
    assert records[1]["judge"] is None
    assert records[1]["judge_error"] is None
    assert summary["judge_summary"]["total_evaluated"] == 1
    assert summary["judge_summary"]["valid_rate"] == 0


def test_evaluate_resume_does_not_repeat_saved_judgments(
    tmp_path, sample_input, valid_plan, monkeypatch
):
    plan_output = json.dumps(
        {"response_type": "plan", "plan": valid_plan.model_dump(mode="json", exclude_none=True)}
    )
    run_dir = tmp_path / "resume-eval"
    write_generations(
        run_dir,
        [
            generation_record("GD-STD-01", sample_input, plan_output),
            generation_record("GD-STD-02", sample_input, plan_output),
        ],
    )
    calls = []

    def fake_judge(session_input, plan, config):
        assert isinstance(plan, TrainingPlanLLM)
        assert isinstance(config, JudgeConfig)
        calls.append(session_input.user_profile.user_id)
        return valid_judge_result()

    monkeypatch.setattr(runner, "judge_plan", fake_judge)
    runner.evaluate_run(run_dir)
    summary = runner.evaluate_run(run_dir, resume=True)

    assert calls == ["GD-STD-01", "GD-STD-02"]
    assert len(runner._read_jsonl(run_dir / "evaluations.jsonl")) == 2
    assert summary["judge_summary"]["total_evaluated"] == 2
