import copy
import json
from pathlib import Path

import pytest

from evaluation.metrics import (
    TimeAssumptions,
    calculate_plan_minutes,
    check_exercise_order,
    check_time_coherence,
    evaluate_output,
    summarize,
)
from schemas.training_plan import TrainingPlanLLM

EXAMPLE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "evaluation"
    / "examples"
    / "training_plan_schema_validation.json"
)
BACKEND_FIELDS = ("session_id", "user_id", "generated_at", "exercise_ids_resolved")
NO_OVERHEAD = TimeAssumptions(
    seconds_per_rep=4, transition_seconds_per_exercise=0, warm_up_minutes=0, cool_down_minutes=0
)


def exercise(priority="Primary", **overrides):
    fields = {
        "name": f"{priority} lift",
        "modality": "Strength",
        "priority": priority,
        "primary_muscle_group": "Chest",
        "sets": 3,
        "reps": "10",
        "rest_seconds": 60,
        "rpe": 8,
        "instructions": ["Control the descent."],
    }
    return {**fields, **overrides}


def make_plan(*items, duration=30, **sections):
    return {
        "title": "Test",
        "main_focus": "Hypertrophy",
        "estimated_duration_minutes": duration,
        "main_block": list(items) or [exercise()],
        **sections,
    }


def as_raw(plan):
    return json.dumps({"response_type": "plan", "plan": plan})


@pytest.fixture
def example_plan():
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    return {key: value for key, value in data.items() if key not in BACKEND_FIELDS}


def test_strength_time_counts_work_and_rest_between_sets():
    plan = TrainingPlanLLM.model_validate(make_plan())
    # 3 sets x 10 reps x 4 s + 2 rests x 60 s = 240 s
    assert calculate_plan_minutes(plan, NO_OVERHEAD) == pytest.approx(4)


def test_rep_range_uses_midpoint():
    plan = TrainingPlanLLM.model_validate(make_plan(exercise(reps="8-12", sets=1)))
    assert calculate_plan_minutes(plan, NO_OVERHEAD) == pytest.approx(40 / 60)


def test_time_includes_optional_sections():
    plan = TrainingPlanLLM.model_validate(
        make_plan(
            warm_up={"general_activation": ["Row"]},
            additional_cardio={"activity_type": "Bike", "duration_minutes": 10, "intensity": "Low"},
            cool_down={"exercises": ["Stretch"], "estimated_duration_minutes": 7},
        )
    )
    assumptions = TimeAssumptions(transition_seconds_per_exercise=0, warm_up_minutes=8)
    assert calculate_plan_minutes(plan, assumptions) == pytest.approx(4 + 8 + 10 + 7)


def test_empty_warm_up_adds_no_time():
    plan = TrainingPlanLLM.model_validate(make_plan(warm_up={}))
    assumptions = TimeAssumptions(transition_seconds_per_exercise=0, warm_up_minutes=8)
    assert calculate_plan_minutes(plan, assumptions) == pytest.approx(4)


def test_mobility_and_cardio_time():
    mobility = exercise(
        priority="Accessory", modality="Mobility", rpe=None, rest_seconds=None, sets=2, reps="5"
    )
    cardio = {
        "name": "Bike", "modality": "Cardio", "priority": "Accessory",
        "duration_minutes": 10, "cardio_intensity": "Low", "instructions": ["Keep pace."],
    }
    plan = TrainingPlanLLM.model_validate(make_plan(mobility, cardio))
    assert calculate_plan_minutes(plan, NO_OVERHEAD) == pytest.approx(40 / 60 + 10)


@pytest.mark.parametrize("duration, expected", [(5, True), (4, True), (2, False), (8, False)])
def test_time_tolerance(duration, expected):
    plan = TrainingPlanLLM.model_validate(make_plan(duration=15))
    plan = plan.model_copy(update={"estimated_duration_minutes": duration})
    assumptions = TimeAssumptions(transition_seconds_per_exercise=0, tolerance=0.25)
    assert check_time_coherence(plan, assumptions).within_tolerance is expected


@pytest.mark.parametrize(
    "priorities, inversions",
    [
        (["Primary", "Secondary", "Accessory"], 0),
        (["Primary", "Primary", "Accessory"], 0),
        (["Secondary", "Primary"], 1),
        (["Accessory", "Secondary", "Primary"], 3),
    ],
)
def test_exercise_order(priorities, inversions):
    plan = TrainingPlanLLM.model_validate(make_plan(*[exercise(p) for p in priorities]))
    result = check_exercise_order(plan)
    assert result.inversions == inversions
    assert result.is_ordered is (inversions == 0)


@pytest.mark.parametrize("raw", ["not json", "```json\n{}\n```", ""])
def test_invalid_json_is_not_repaired(raw):
    result = evaluate_output(raw)
    assert (result.json_valid, result.schema_valid, result.response_type) == (False, False, None)


@pytest.mark.parametrize(
    "raw", ["[]", "{}", json.dumps({"response_type": "plan", "plan": {"title": "x"}})]
)
def test_schema_failure_is_reported(raw):
    result = evaluate_output(raw)
    assert result.json_valid is True
    assert result.schema_valid is False
    assert result.schema_error_count > 0


def test_non_plan_response_skips_plan_metrics():
    raw = json.dumps({"response_type": "out_of_scope", "message": "Fuera de alcance."})
    result = evaluate_output(raw)
    assert result.response_type == "out_of_scope"
    assert result.time_coherence is None
    assert result.order is None


def test_plan_reports_scope_violation(example_plan):
    data = copy.deepcopy(example_plan)
    data["additional_cardio"] = {
        "activity_type": "Bike",
        "duration_minutes": 10,
        "intensity": "Low",
    }
    assert evaluate_output(as_raw(data)).scope_violations == (
        "Additional cardio is not enabled in this scope.",
    )


def test_summary_keeps_failures_in_denominators():
    ordered = as_raw(
        make_plan(exercise("Primary"), exercise("Primary"), exercise("Accessory"), duration=15)
    )
    unordered = as_raw(make_plan(exercise("Accessory"), exercise("Primary"), duration=30))
    results = [
        evaluate_output(ordered),
        evaluate_output(unordered),
        evaluate_output(json.dumps({"response_type": "clarification", "questions": ["¿Qué?"]})),
        evaluate_output("not json"),
    ]
    summary = summarize(results)
    assert summary.total == 4
    assert summary.json_valid_rate == pytest.approx(0.75)
    assert summary.schema_valid_rate == pytest.approx(0.75)
    assert summary.response_type_counts == {"plan": 2, "clarification": 1, "invalid": 1}
    assert summary.plans == 2
    assert summary.order_compliance_rate == pytest.approx(0.5)
    assert summary.time_coherence_rate == pytest.approx(0.5)
    assert summary.scope_compliance_rate == pytest.approx(1)


def test_summary_without_plans_has_no_plan_rates():
    summary = summarize([evaluate_output("not json")])
    assert summary.plans == 0
    assert summary.time_coherence_rate is None
    assert summary.mean_absolute_time_error is None
    assert summarize([]).json_valid_rate is None
