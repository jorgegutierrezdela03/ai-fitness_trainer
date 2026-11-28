"""CLI runner for generating and evaluating reproducible experiment runs."""

import argparse
import json
import re
import sys
from collections.abc import Sequence
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from baseline.generator import (
    GenerationResult,
    OllamaConfig,
    OllamaUnavailableError,
    generate_session,
)
from evaluation.judge import (
    JudgeConfig,
    JudgeEvaluation,
    JudgeResult,
    judge_plan,
    summarize_judgments,
)
from evaluation.metrics import OutputEvaluation, evaluate_output, summarize
from schemas.llm_response import LLM_RESPONSE_ADAPTER, PlanResponse
from schemas.user_profile import SessionGenerationInput

DEFAULT_DATASET = Path("data/golden_dataset/golden_dataset.json")
DEFAULT_RUNS_DIR = Path("data/evaluation/runs")
CATEGORIES = ("STD", "CMP", "AMB", "SAF", "OOS")
CASE_ID_PATTERN = re.compile(r"GD-([A-Z]{3})-\d+")
RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def _category_for_case(case_id: str) -> str:
    match = CASE_ID_PATTERN.fullmatch(case_id)
    return match.group(1) if match else "UNKNOWN"


def _load_dataset(path: Path) -> list[tuple[str, str, SessionGenerationInput]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Dataset must contain a JSON array: {path}")

    cases = []
    seen_case_ids = set()
    for index, item in enumerate(data, start=1):
        try:
            session_input = SessionGenerationInput.model_validate(item)
        except ValidationError as error:
            raise ValueError(f"Invalid dataset input at item {index}: {error}") from error
        case_id = session_input.user_profile.user_id
        if not case_id:
            raise ValueError(f"Dataset item {index} is missing user_profile.user_id.")
        if case_id in seen_case_ids:
            raise ValueError(f"Duplicate case_id in dataset: {case_id}")
        seen_case_ids.add(case_id)
        cases.append((case_id, _category_for_case(case_id), session_input))
    return cases


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {error}") from error
            if not isinstance(record, dict):
                raise ValueError(f"Expected a JSON object at {path}:{line_number}.")
            records.append(record)
    return records


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
        file.flush()


def _safe_run_id(run_id: str) -> str:
    if not RUN_ID_PATTERN.fullmatch(run_id) or run_id in {".", ".."}:
        raise ValueError("run_id must contain only letters, numbers, '.', '_' or '-'.")
    return run_id


def _generated_run_id(model: str) -> str:
    safe_model = re.sub(r"[^A-Za-z0-9._-]+", "_", model).strip("._-") or "model"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{safe_model}"


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _ensure_generate_run(
    run_dir: Path,
    run_config: dict[str, Any],
    resume: bool,
) -> None:
    if run_dir.exists() and not resume:
        raise FileExistsError(f"Run directory already exists; use --resume: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)

    config_path = run_dir / "run_config.json"
    generations_path = run_dir / "generations.jsonl"
    if resume and generations_path.exists() and not config_path.exists():
        raise ValueError(f"Cannot resume without run_config.json in {run_dir}.")
    if resume and config_path.exists():
        existing = json.loads(config_path.read_text(encoding="utf-8"))
        for key in ("dataset", "model", "temperature", "seed"):
            if existing.get(key) != run_config[key]:
                raise ValueError(f"Cannot resume run with a different {key}.")
    elif not config_path.exists():
        _write_json(config_path, run_config)


def generate_run(
    dataset: Path = DEFAULT_DATASET,
    runs_dir: Path = DEFAULT_RUNS_DIR,
    run_id: str | None = None,
    model: str | None = None,
    limit: int | None = None,
    resume: bool = False,
) -> Path:
    if limit is not None and limit < 1:
        raise ValueError("--limit must be a positive integer.")
    if resume and run_id is None:
        raise ValueError("--resume requires --run-id so the run can be identified.")

    cases = _load_dataset(dataset)
    if limit is not None:
        cases = cases[:limit]

    config = OllamaConfig.from_env()
    if model is not None:
        config = replace(config, model=model)
    selected_run_id = _safe_run_id(run_id or _generated_run_id(config.model))
    run_dir = runs_dir / selected_run_id
    run_config = {
        "run_id": selected_run_id,
        "dataset": str(dataset.resolve()),
        "model": config.model,
        "temperature": config.temperature,
        "seed": config.seed,
        "timeout_seconds": config.timeout_seconds,
        "limit": limit,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _ensure_generate_run(run_dir, run_config, resume)

    generations_path = run_dir / "generations.jsonl"
    previous_records = _read_jsonl(generations_path)
    completed_case_ids = {record.get("case_id") for record in previous_records}
    if len(completed_case_ids) != len(previous_records):
        raise ValueError(f"Duplicate case_id in {generations_path}.")

    for case_id, category, session_input in cases:
        if case_id in completed_case_ids:
            continue
        session_input_data = session_input.model_dump(mode="json", exclude_none=True)
        try:
            result: GenerationResult = generate_session(session_input, config)
            record = {
                "case_id": case_id,
                "category": category,
                "session_input": session_input_data,
                "raw_output": result.raw_output,
                "is_valid": result.is_valid,
                "validation_errors": result.validation_errors,
                "metadata": {
                    "model": result.model,
                    "latency_seconds": result.latency_seconds,
                },
                "error": None,
            }
        except OllamaUnavailableError as error:
            record = {
                "case_id": case_id,
                "category": category,
                "session_input": session_input_data,
                "raw_output": "",
                "is_valid": False,
                "validation_errors": [],
                "metadata": {"model": config.model},
                "error": str(error),
            }
        _append_jsonl(generations_path, record)
        completed_case_ids.add(case_id)

    return run_dir


def _serialize_judge_result(result: JudgeResult) -> dict[str, Any]:
    return {
        "is_valid": result.is_valid,
        "judgment": result.judgment.model_dump(mode="json") if result.judgment else None,
        "raw_output": result.raw_output,
        "validation_errors": result.validation_errors,
        "metadata": result.metadata,
    }


def _deserialize_judge_result(value: dict[str, Any]) -> JudgeResult:
    judgment_data = value.get("judgment")
    judgment = JudgeEvaluation.model_validate(judgment_data) if judgment_data else None
    return JudgeResult(
        is_valid=value["is_valid"],
        judgment=judgment,
        raw_output=value["raw_output"],
        validation_errors=value["validation_errors"],
        metadata=value["metadata"],
    )


def _failed_judge_result(error: str, model: str) -> JudgeResult:
    return JudgeResult(
        is_valid=False,
        judgment=None,
        raw_output="",
        validation_errors=[{"location": "", "message": error}],
        metadata={"model": model},
    )


def _evaluation_record(
    generation: dict[str, Any],
    deterministic: OutputEvaluation,
    judge: JudgeResult | None,
    judge_error: str | None,
) -> dict[str, Any]:
    return {
        "case_id": generation["case_id"],
        "category": generation.get("category", _category_for_case(generation["case_id"])),
        "session_input": generation["session_input"],
        "raw_output": generation.get("raw_output", ""),
        "deterministic": asdict(deterministic),
        "judge": _serialize_judge_result(judge) if judge else None,
        "judge_error": judge_error,
    }


def _summary_dict(
    deterministic_results: Sequence[OutputEvaluation],
    judge_results: Sequence[JudgeResult],
    skip_judge: bool,
) -> dict[str, Any]:
    return {
        "deterministic_summary": asdict(summarize(deterministic_results)),
        "judge_summary": (
            asdict(summarize_judgments(judge_results)) if not skip_judge else None
        ),
    }


def evaluate_run(
    run_dir: Path,
    skip_judge: bool = False,
    judge_model: str | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    generations_path = run_dir / "generations.jsonl"
    if not generations_path.exists():
        raise FileNotFoundError(f"Missing generations.jsonl in {run_dir}.")
    evaluations_path = run_dir / "evaluations.jsonl"
    if evaluations_path.exists() and not resume:
        raise FileExistsError(f"Evaluations already exist; use --resume: {evaluations_path}")

    generations = _read_jsonl(generations_path)
    generation_ids = [record.get("case_id") for record in generations]
    if any(not isinstance(case_id, str) or not case_id for case_id in generation_ids):
        raise ValueError(f"Every generation in {generations_path} must have a case_id.")
    if len(set(generation_ids)) != len(generation_ids):
        raise ValueError(f"Duplicate case_id in {generations_path}.")

    prior_evaluations = _read_jsonl(evaluations_path)
    evaluated_by_id = {}
    for record in prior_evaluations:
        case_id = record.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"Every evaluation in {evaluations_path} must have a case_id.")
        if case_id in evaluated_by_id:
            raise ValueError(f"Duplicate case_id in {evaluations_path}: {case_id}")
        evaluated_by_id[case_id] = record

    judge_config = JudgeConfig.from_env()
    if judge_model is not None:
        judge_config = replace(judge_config, model=judge_model)

    deterministic_by_id: dict[str, OutputEvaluation] = {}
    judge_by_id: dict[str, JudgeResult | None] = {}
    mode = "a" if resume else "w"
    with evaluations_path.open(mode, encoding="utf-8") as output_file:
        for generation in generations:
            case_id = generation["case_id"]
            category = generation.get("category", _category_for_case(case_id))
            try:
                session_input = SessionGenerationInput.model_validate(generation["session_input"])
            except (KeyError, ValidationError) as error:
                raise ValueError(f"Invalid session_input for case {case_id}: {error}") from error
            raw_output = generation.get("raw_output", "")
            if not isinstance(raw_output, str):
                raise ValueError(f"raw_output for case {case_id} must be a string.")

            deterministic = evaluate_output(raw_output, session_input=session_input)
            deterministic_by_id[case_id] = deterministic
            existing = evaluated_by_id.get(case_id)
            if existing is not None:
                judge_by_id[case_id] = _existing_judge_result(existing, judge_config.model)
                continue

            judgment = None
            judge_error = None
            if (
                not skip_judge
                and deterministic.schema_valid
                and deterministic.response_type == "plan"
            ):
                parsed = LLM_RESPONSE_ADAPTER.validate_python(json.loads(raw_output))
                if not isinstance(parsed, PlanResponse):
                    raise ValueError(f"Expected a validated plan for case {case_id}.")
                try:
                    judgment = judge_plan(session_input, parsed.plan, judge_config)
                except OllamaUnavailableError as error:
                    judge_error = str(error)

            record = _evaluation_record(
                {**generation, "category": category},
                deterministic,
                judgment,
                judge_error,
            )
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            output_file.flush()
            evaluated_by_id[case_id] = record
            judge_by_id[case_id] = (
                judgment if judgment is not None else
                _failed_judge_result(judge_error, judge_config.model)
                if judge_error is not None
                else None
            )

    categories = list(CATEGORIES)
    observed_categories = {
        record.get("category", _category_for_case(record["case_id"]))
        for record in generations
    }
    categories.extend(sorted(observed_categories.difference(CATEGORIES)))

    deterministic_results = list(deterministic_by_id.values())
    judge_results = [
        result for result in judge_by_id.values() if result is not None
    ]
    summary = _summary_dict(deterministic_results, judge_results, skip_judge)
    by_category = {}
    for category in categories:
        case_ids = [
            record["case_id"]
            for record in generations
            if record.get("category", _category_for_case(record["case_id"])) == category
        ]
        category_deterministic = [deterministic_by_id[case_id] for case_id in case_ids]
        category_judges = [
            judge_by_id[case_id]
            for case_id in case_ids
            if judge_by_id.get(case_id) is not None
        ]
        by_category[category] = _summary_dict(
            category_deterministic, category_judges, skip_judge
        )
    summary["by_category"] = by_category
    _write_json(run_dir / "summary.json", summary)
    return summary


def _existing_judge_result(
    evaluation: dict[str, Any], model: str
) -> JudgeResult | None:
    if evaluation.get("judge") is not None:
        return _deserialize_judge_result(evaluation["judge"])
    error = evaluation.get("judge_error")
    return _failed_judge_result(error, model) if error else None


def _positive_int(value: str) -> int:
    try:
        result = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error
    if result < 1:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and evaluate experiment runs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate outputs for a dataset.")
    generate_parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    generate_parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    generate_parser.add_argument("--run-id")
    generate_parser.add_argument("--model")
    generate_parser.add_argument("--limit", type=_positive_int)
    generate_parser.add_argument("--resume", action="store_true")

    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate a generation run.")
    evaluate_parser.add_argument("--run-dir", type=Path, required=True)
    evaluate_parser.add_argument("--skip-judge", action="store_true")
    evaluate_parser.add_argument("--judge-model")
    evaluate_parser.add_argument("--resume", action="store_true")
    return parser


def _print_summary(summary: dict[str, Any]) -> None:
    deterministic = summary["deterministic_summary"]
    print(
        f"Evaluated {deterministic['total']} cases; "
        f"{deterministic['plans']} valid plans; "
        f"JSON rate: {deterministic['json_valid_rate']!s}; "
        f"schema rate: {deterministic['schema_valid_rate']!s}."
    )
    judge = summary["judge_summary"]
    if judge is not None:
        print(
            f"Judge: {judge['total_evaluated']} attempted; "
            f"valid rate: {judge['valid_rate']!s}; "
            f"profile alignment mean: {judge['profile_alignment_mean']!s}."
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            run_dir = generate_run(
                dataset=args.dataset,
                runs_dir=args.runs_dir,
                run_id=args.run_id,
                model=args.model,
                limit=args.limit,
                resume=args.resume,
            )
            count = len(_read_jsonl(run_dir / "generations.jsonl"))
            print(f"Generated records: {count}. Run directory: {run_dir}")
        else:
            summary = evaluate_run(
                run_dir=args.run_dir,
                skip_judge=args.skip_judge,
                judge_model=args.judge_model,
                resume=args.resume,
            )
            _print_summary(summary)
        return 0
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    sys.exit(main())
