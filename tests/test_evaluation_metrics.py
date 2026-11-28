import copy
import json
from pathlib import Path

import pytest

from evaluation.metrics import (
    ACTIVE_SCOPE,
    INJURY_MUSCLE_GROUPS,
    AvailableTimeAssumptions,
    TimeAssumptions,
    VolumeAssumptions,
    calculate_plan_minutes,
    check_available_time_coherence,
    check_exercise_order,
    check_exercise_uniqueness,
    check_injury_conflicts,
    check_level_extremes,
    check_time_coherence,
    check_volume_sanity,
    evaluate_output,
    summarize,
)
from schemas.training_plan import TrainingPlanLLM
from schemas.user_profile import SessionGenerationInput

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


def make_session_input(
    *,
    duration=60,
    experience_level="Intermediate",
    affected_areas=None,
):
    affected_areas = affected_areas or []
    return SessionGenerationInput.model_validate(
        {
            "user_profile": {
                "age": 28,
                "experience_level": experience_level,
                "primary_goals": ["Strength"],
                "available_days_per_week": 3,
                "session_duration_minutes": duration,
                "physical_limitations": {
                    "has_limitations": bool(affected_areas),
                    "affected_areas": affected_areas,
                },
            },
            "session_request": "Create a training session.",
        }
    )


class SessionInputWithDurationOverride(SessionGenerationInput):
    session_duration_minutes: int


def make_session_input_with_override(duration, *, profile_duration=60):
    base = make_session_input(duration=profile_duration)
    return SessionInputWithDurationOverride.model_validate(
        {**base.model_dump(), "session_duration_minutes": duration}
    )


def cardio_exercise(name="Bike", duration=40):
    return {
        "name": name,
        "modality": "Cardio",
        "priority": "Primary",
        "duration_minutes": duration,
        "cardio_intensity": "Low",
        "instructions": ["Maintain an easy pace."],
    }


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
    assert evaluate_output(as_raw(data), ACTIVE_SCOPE, NO_OVERHEAD).scope_violations == (
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


def test_volume_sanity_accepts_threshold_boundaries():
    plan = TrainingPlanLLM.model_validate(make_plan(exercise(sets=4), duration=30))
    result = check_volume_sanity(plan)
    assert result.total_strength_sets == 4
    assert result.sets_by_muscle_group == (("Chest", 4),)
    assert result.is_sane


def test_volume_sanity_flags_extreme_total_and_per_muscle_group():
    low_plan = TrainingPlanLLM.model_validate(make_plan(exercise(sets=3)))
    high_plan = TrainingPlanLLM.model_validate(
        make_plan(
            *[exercise("Primary", name=f"Lift {index}", sets=11) for index in range(3)]
        )
    )
    muscle_plan = TrainingPlanLLM.model_validate(
        make_plan(*[exercise(name=f"Lift {index}", sets=3) for index in range(6)])
    )

    assert not check_volume_sanity(low_plan).is_sane
    assert check_volume_sanity(low_plan).total_strength_sets == 3
    assert any("exceed 30" in item for item in check_volume_sanity(high_plan).violations)
    muscle_result = check_volume_sanity(muscle_plan)
    assert muscle_result.total_strength_sets == 18
    assert muscle_result.sets_by_muscle_group == (("Chest", 18),)
    assert any("Chest" in item for item in muscle_result.violations)
    boundary_plan = TrainingPlanLLM.model_validate(
        make_plan(*[exercise(name=f"Lift {index}", sets=4) for index in range(4)])
    )
    boundary_result = check_volume_sanity(boundary_plan)
    assert boundary_result.total_strength_sets == 16
    assert boundary_result.is_sane


def test_volume_sanity_thresholds_are_configurable():
    plan = TrainingPlanLLM.model_validate(make_plan(exercise(sets=3)))
    result = check_volume_sanity(
        plan,
        VolumeAssumptions(
            minimum_strength_sets=3,
            maximum_strength_sets=10,
            maximum_sets_per_muscle_group=10,
        ),
    )
    assert result.is_sane


def test_exercise_uniqueness_uses_normalized_names():
    unique_plan = TrainingPlanLLM.model_validate(
        make_plan(exercise(name="Bench Press"), exercise(name="Barbell Row"), duration=30)
    )
    plan = TrainingPlanLLM.model_validate(
        make_plan(
            exercise(name="Bench Press"),
            exercise(name="  BENCH   press "),
            exercise(name="Row"),
            duration=30,
        )
    )
    assert check_exercise_uniqueness(unique_plan).is_unique
    result = check_exercise_uniqueness(plan)
    assert not result.is_unique
    assert result.duplicates == ("bench press",)


def test_available_time_coherence_uses_session_override_before_profile():
    plan = TrainingPlanLLM.model_validate(make_plan(cardio_exercise(), duration=40))
    profile_only = make_session_input(duration=60)
    with_override = make_session_input_with_override(100, profile_duration=60)

    profile_result = check_available_time_coherence(plan, profile_only, NO_OVERHEAD)
    override_result = check_available_time_coherence(plan, with_override, NO_OVERHEAD)

    assert profile_result.available_minutes == 60
    assert profile_result.is_coherent
    assert override_result.available_minutes == 100
    assert not override_result.is_coherent


@pytest.mark.parametrize(
    "available, duration, expected",
    [(80, 40, True), (100, 135, True), (100, 136, False), (100, 49, False)],
)
def test_available_time_coherence_extreme_thresholds(available, duration, expected):
    if duration > 120:
        plan_data = make_plan(
            cardio_exercise(duration=120),
            duration=30,
            warm_up={"general_activation": ["Easy movement"]},
            cool_down={
                "exercises": ["Stretch"],
                "estimated_duration_minutes": duration - 129,
            },
        )
    else:
        plan_data = make_plan(cardio_exercise(duration=duration), duration=30)
    plan = TrainingPlanLLM.model_validate(plan_data)
    time_assumptions = TimeAssumptions() if duration > 120 else NO_OVERHEAD
    result = check_available_time_coherence(
        plan,
        make_session_input(duration=available),
        time_assumptions,
        AvailableTimeAssumptions(),
    )
    assert result.is_coherent is expected


def test_level_extremes_only_flags_beginner_volume_and_primary_rpe():
    beginner = make_session_input(experience_level="Beginner")
    other_level = make_session_input(experience_level="Advanced")
    high_volume_and_rpe = TrainingPlanLLM.model_validate(
        make_plan(
            exercise("Primary", name="Lift A", sets=11, rpe=10),
            exercise("Primary", name="Lift B", sets=10, rpe=8),
            duration=30,
        )
    )

    beginner_result = check_level_extremes(high_volume_and_rpe, beginner)
    advanced_result = check_level_extremes(high_volume_and_rpe, other_level)

    assert beginner_result.total_strength_sets == 21
    assert len(beginner_result.violations) == 2
    assert not beginner_result.is_within_limits
    assert advanced_result.is_within_limits
    assert advanced_result.violations == ()


def test_injury_conflicts_use_explicit_primary_muscle_mapping():
    shoulder_input = make_session_input(affected_areas=["Shoulder"])
    conflicting_plan = TrainingPlanLLM.model_validate(
        make_plan(exercise(name="Shoulder Press", primary_muscle_group="Shoulders"))
    )
    unrelated_plan = TrainingPlanLLM.model_validate(
        make_plan(exercise(name="Bench Press", primary_muscle_group="Chest"))
    )

    conflicts = check_injury_conflicts(conflicting_plan, shoulder_input)
    unrelated = check_injury_conflicts(unrelated_plan, shoulder_input)

    assert not conflicts.is_compatible
    assert conflicts.conflicts == (
        "Shoulder Press (Shoulders) conflicts with affected area Shoulder.",
    )
    assert unrelated.is_compatible
    assert unrelated.conflicts == ()


def test_injury_conflicts_ignore_areas_missing_from_mapping(monkeypatch):
    session_input = make_session_input(affected_areas=["Shoulder"])
    plan = TrainingPlanLLM.model_validate(
        make_plan(exercise(name="Shoulder Press", primary_muscle_group="Shoulders"))
    )
    monkeypatch.delitem(INJURY_MUSCLE_GROUPS, "Shoulder")

    result = check_injury_conflicts(plan, session_input)

    assert result.is_compatible
    assert result.conflicts == ()


def test_new_metrics_are_none_without_user_input_or_for_non_plan():
    no_context = evaluate_output(as_raw(make_plan(exercise(sets=4))))
    with_positional_context = evaluate_output(
        as_raw(make_plan(exercise(sets=4))), make_session_input()
    )
    non_plan = evaluate_output(
        json.dumps({"response_type": "clarification", "questions": ["How long?"]}),
        session_input=make_session_input(),
    )

    assert no_context.volume_sanity is not None
    assert no_context.exercise_uniqueness is not None
    assert no_context.available_time_coherence is None
    assert no_context.level_extremes is None
    assert no_context.injury_conflicts is None
    assert with_positional_context.available_time_coherence is not None
    assert with_positional_context.level_extremes is not None
    assert with_positional_context.injury_conflicts is not None
    assert non_plan.volume_sanity is None
    assert non_plan.exercise_uniqueness is None
    assert non_plan.available_time_coherence is None
    assert non_plan.level_extremes is None
    assert non_plan.injury_conflicts is None


def test_summary_aggregates_new_metrics_with_correct_denominators():
    duplicate_plan = make_plan(cardio_exercise(), cardio_exercise(), duration=40)
    context_input = make_session_input(duration=50, experience_level="Beginner")
    evaluations = [
        evaluate_output(as_raw(duplicate_plan), session_input=context_input),
        evaluate_output(as_raw(duplicate_plan)),
        evaluate_output(json.dumps({"response_type": "clarification", "questions": ["Why?"]})),
        evaluate_output("{}"),
        evaluate_output("not json"),
    ]

    summary = summarize(evaluations)

    assert summary.plans == 2
    assert summary.volume_sanity_rate == 0
    assert summary.exercise_uniqueness_rate == 0
    assert summary.available_time_coherence_rate == 0
    assert summary.level_compliance_rate == 1
    assert summary.injury_compatibility_rate == 1


def test_summary_new_rates_are_none_without_eligible_plans():
    summary = summarize(
        [
            evaluate_output("not json"),
            evaluate_output(json.dumps({"response_type": "out_of_scope", "message": "No."})),
        ]
    )
    assert summary.volume_sanity_rate is None
    assert summary.exercise_uniqueness_rate is None
    assert summary.available_time_coherence_rate is None
    assert summary.level_compliance_rate is None
    assert summary.injury_compatibility_rate is None
