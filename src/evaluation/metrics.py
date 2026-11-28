"""Deterministic post-hoc checks for LLM outputs and optional user context.

Raw output is never repaired, and invalid outputs stay in aggregate denominators so that
failures cannot be excluded silently.
"""

import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import overload

from pydantic import ValidationError

from schemas.llm_response import LLM_RESPONSE_ADAPTER, PlanResponse
from schemas.scope import ACTIVE_SCOPE, TrainingScope
from schemas.training_plan import ExerciseItem, TrainingPlanLLM
from schemas.user_profile import SessionGenerationInput

PRIORITY_RANK = {"Primary": 0, "Secondary": 1, "Accessory": 2}
INJURY_MUSCLE_GROUPS = {
    "Shoulder": frozenset({"Shoulders"}),
    "Elbow": frozenset({"Biceps", "Triceps"}),
    "Wrist": frozenset(),
    "Back": frozenset({"Back"}),
    "Hip": frozenset({"Glutes"}),
    "Knee": frozenset({"Quadriceps"}),
    "Ankle": frozenset({"Calves"}),
    "Other": frozenset(),
}


@dataclass(frozen=True)
class TimeAssumptions:
    """Provisional estimation parameters. Changing them requires a new evaluation version."""

    seconds_per_rep: float = 4.0
    transition_seconds_per_exercise: float = 60.0
    warm_up_minutes: float = 8.0
    cool_down_minutes: float = 5.0
    tolerance: float = 0.20


DEFAULT_TIME_ASSUMPTIONS = TimeAssumptions()


@dataclass(frozen=True)
class VolumeAssumptions:
    minimum_strength_sets: int = 4
    maximum_strength_sets: int = 30
    maximum_sets_per_muscle_group: int = 16
    beginner_maximum_strength_sets: int = 20


DEFAULT_VOLUME_ASSUMPTIONS = VolumeAssumptions()


@dataclass(frozen=True)
class AvailableTimeAssumptions:
    maximum_overage_ratio: float = 0.35
    minimum_available_time_ratio: float = 0.50


DEFAULT_AVAILABLE_TIME_ASSUMPTIONS = AvailableTimeAssumptions()


@dataclass(frozen=True)
class TimeCoherence:
    declared_minutes: int
    calculated_minutes: float
    relative_error: float
    within_tolerance: bool


@dataclass(frozen=True)
class OrderCheck:
    inversions: int
    is_ordered: bool


@dataclass(frozen=True)
class VolumeSanity:
    total_strength_sets: int
    sets_by_muscle_group: tuple[tuple[str, int], ...]
    violations: tuple[str, ...]
    is_sane: bool


@dataclass(frozen=True)
class ExerciseUniqueness:
    duplicates: tuple[str, ...]
    is_unique: bool


@dataclass(frozen=True)
class AvailableTimeCoherence:
    available_minutes: int
    calculated_minutes: float
    relative_ratio: float
    is_coherent: bool


@dataclass(frozen=True)
class LevelExtremes:
    total_strength_sets: int
    violations: tuple[str, ...]
    is_within_limits: bool


@dataclass(frozen=True)
class InjuryConflicts:
    conflicts: tuple[str, ...]
    is_compatible: bool


@dataclass(frozen=True)
class OutputEvaluation:
    json_valid: bool
    schema_valid: bool
    schema_error_count: int
    response_type: str | None
    scope_violations: tuple[str, ...] = ()
    time_coherence: TimeCoherence | None = None
    order: OrderCheck | None = None
    volume_sanity: VolumeSanity | None = None
    exercise_uniqueness: ExerciseUniqueness | None = None
    available_time_coherence: AvailableTimeCoherence | None = None
    level_extremes: LevelExtremes | None = None
    injury_conflicts: InjuryConflicts | None = None


@dataclass(frozen=True)
class EvaluationSummary:
    total: int
    json_valid_rate: float | None
    schema_valid_rate: float | None
    response_type_counts: dict[str, int]
    plans: int
    scope_compliance_rate: float | None
    time_coherence_rate: float | None
    mean_absolute_time_error: float | None
    order_compliance_rate: float | None
    volume_sanity_rate: float | None = None
    exercise_uniqueness_rate: float | None = None
    available_time_coherence_rate: float | None = None
    level_compliance_rate: float | None = None
    injury_compatibility_rate: float | None = None


def _mean_reps(reps: str) -> float:
    bounds = [int(value) for value in reps.split("-")]
    return sum(bounds) / len(bounds)


def _exercise_seconds(exercise: ExerciseItem, assumptions: TimeAssumptions) -> float:
    if exercise.duration_minutes is not None:
        work = exercise.duration_minutes * 60.0
    else:
        sets = exercise.sets or 1
        work = sets * _mean_reps(exercise.reps) * assumptions.seconds_per_rep
        work += max(sets - 1, 0) * (exercise.rest_seconds or 0)
    return work + assumptions.transition_seconds_per_exercise


def calculate_plan_minutes(
    plan: TrainingPlanLLM, assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS
) -> float:
    minutes = sum(_exercise_seconds(item, assumptions) for item in plan.main_block) / 60.0
    warm_up = plan.warm_up
    if warm_up and (warm_up.general_activation or warm_up.specific_warmup or warm_up.warmup_sets):
        minutes += assumptions.warm_up_minutes
    if plan.additional_cardio:
        minutes += plan.additional_cardio.duration_minutes
    if plan.cool_down:
        minutes += plan.cool_down.estimated_duration_minutes or assumptions.cool_down_minutes
    return minutes


def check_time_coherence(
    plan: TrainingPlanLLM, assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS
) -> TimeCoherence:
    declared = plan.estimated_duration_minutes
    calculated = calculate_plan_minutes(plan, assumptions)
    relative_error = (calculated - declared) / declared
    return TimeCoherence(
        declared_minutes=declared,
        calculated_minutes=round(calculated, 2),
        relative_error=round(relative_error, 4),
        within_tolerance=abs(relative_error) <= assumptions.tolerance,
    )


def check_exercise_order(plan: TrainingPlanLLM) -> OrderCheck:
    """Counts pairs where a less important exercise comes before a more important one."""
    ranks = [PRIORITY_RANK[exercise.priority] for exercise in plan.main_block]
    inversions = sum(
        earlier > later
        for index, earlier in enumerate(ranks)
        for later in ranks[index + 1 :]
    )
    return OrderCheck(inversions=inversions, is_ordered=inversions == 0)


def check_volume_sanity(
    plan: TrainingPlanLLM,
    assumptions: VolumeAssumptions = DEFAULT_VOLUME_ASSUMPTIONS,
) -> VolumeSanity:
    sets_by_muscle_group: Counter[str] = Counter()
    total_strength_sets = 0
    for exercise in plan.main_block:
        if exercise.modality != "Strength":
            continue
        exercise_sets = exercise.sets or 0
        total_strength_sets += exercise_sets
        if exercise.primary_muscle_group is not None:
            sets_by_muscle_group[exercise.primary_muscle_group] += exercise_sets

    violations = []
    if total_strength_sets < assumptions.minimum_strength_sets:
        violations.append(
            f"Total strength sets ({total_strength_sets}) are below "
            f"{assumptions.minimum_strength_sets}."
        )
    if total_strength_sets > assumptions.maximum_strength_sets:
        violations.append(
            f"Total strength sets ({total_strength_sets}) exceed "
            f"{assumptions.maximum_strength_sets}."
        )
    violations.extend(
        f"{muscle_group} has {sets} strength sets, exceeding "
        f"{assumptions.maximum_sets_per_muscle_group}."
        for muscle_group, sets in sorted(sets_by_muscle_group.items())
        if sets > assumptions.maximum_sets_per_muscle_group
    )
    return VolumeSanity(
        total_strength_sets=total_strength_sets,
        sets_by_muscle_group=tuple(sorted(sets_by_muscle_group.items())),
        violations=tuple(violations),
        is_sane=not violations,
    )


def check_exercise_uniqueness(plan: TrainingPlanLLM) -> ExerciseUniqueness:
    seen: set[str] = set()
    duplicates: list[str] = []
    for exercise in plan.main_block:
        normalized_name = " ".join(exercise.name.lower().split())
        if normalized_name in seen and normalized_name not in duplicates:
            duplicates.append(normalized_name)
        seen.add(normalized_name)
    return ExerciseUniqueness(duplicates=tuple(duplicates), is_unique=not duplicates)


def _available_session_minutes(session_input: SessionGenerationInput) -> int:
    # SessionGenerationInput currently has no per-session duration override.
    override = getattr(session_input, "session_duration_minutes", None)
    if type(override) is int and override > 0:
        return override
    return session_input.user_profile.session_duration_minutes


def check_available_time_coherence(
    plan: TrainingPlanLLM,
    session_input: SessionGenerationInput,
    time_assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS,
    assumptions: AvailableTimeAssumptions = DEFAULT_AVAILABLE_TIME_ASSUMPTIONS,
) -> AvailableTimeCoherence:
    available_minutes = _available_session_minutes(session_input)
    calculated_minutes = calculate_plan_minutes(plan, time_assumptions)
    relative_ratio = calculated_minutes / available_minutes
    is_coherent = (
        relative_ratio <= 1 + assumptions.maximum_overage_ratio
        and relative_ratio >= assumptions.minimum_available_time_ratio
    )
    return AvailableTimeCoherence(
        available_minutes=available_minutes,
        calculated_minutes=round(calculated_minutes, 2),
        relative_ratio=round(relative_ratio, 4),
        is_coherent=is_coherent,
    )


def _total_strength_sets(plan: TrainingPlanLLM) -> int:
    return sum(
        exercise.sets or 0 for exercise in plan.main_block if exercise.modality == "Strength"
    )


def check_level_extremes(
    plan: TrainingPlanLLM,
    session_input: SessionGenerationInput,
    assumptions: VolumeAssumptions = DEFAULT_VOLUME_ASSUMPTIONS,
) -> LevelExtremes:
    total_strength_sets = _total_strength_sets(plan)
    if session_input.user_profile.experience_level != "Beginner":
        return LevelExtremes(
            total_strength_sets=total_strength_sets, violations=(), is_within_limits=True
        )

    violations = []
    if total_strength_sets > assumptions.beginner_maximum_strength_sets:
        violations.append(
            f"Beginner plan has {total_strength_sets} strength sets, exceeding "
            f"{assumptions.beginner_maximum_strength_sets}."
        )
    violations.extend(
        f"Beginner plan has RPE 10 for primary exercise: {exercise.name}."
        for exercise in plan.main_block
        if exercise.modality == "Strength"
        and exercise.priority == "Primary"
        and exercise.rpe == 10
    )
    return LevelExtremes(
        total_strength_sets=total_strength_sets,
        violations=tuple(violations),
        is_within_limits=not violations,
    )


def check_injury_conflicts(
    plan: TrainingPlanLLM, session_input: SessionGenerationInput
) -> InjuryConflicts:
    affected_areas = session_input.user_profile.physical_limitations.affected_areas or []
    conflicts = []
    for exercise in plan.main_block:
        if exercise.primary_muscle_group is None:
            continue
        for area in affected_areas:
            if exercise.primary_muscle_group in INJURY_MUSCLE_GROUPS.get(area, frozenset()):
                conflicts.append(
                    f"{exercise.name} ({exercise.primary_muscle_group}) conflicts with "
                    f"affected area {area}."
                )
    return InjuryConflicts(conflicts=tuple(conflicts), is_compatible=not conflicts)


@overload
def evaluate_output(
    raw_output: str,
    session_input: SessionGenerationInput | None = None,
    *,
    scope: TrainingScope = ACTIVE_SCOPE,
    assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS,
) -> OutputEvaluation: ...


@overload
def evaluate_output(
    raw_output: str,
    scope: TrainingScope,
    assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS,
) -> OutputEvaluation: ...


def evaluate_output(
    raw_output: str,
    session_input: SessionGenerationInput | TrainingScope | None = None,
    assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS,
    *,
    scope: TrainingScope = ACTIVE_SCOPE,
) -> OutputEvaluation:
    if isinstance(session_input, TrainingScope):
        scope, session_input = session_input, None

    try:
        parsed = json.loads(raw_output)
    except (json.JSONDecodeError, TypeError):
        return OutputEvaluation(
            json_valid=False, schema_valid=False, schema_error_count=0, response_type=None
        )

    try:
        response = LLM_RESPONSE_ADAPTER.validate_python(parsed)
    except ValidationError as error:
        return OutputEvaluation(
            json_valid=True,
            schema_valid=False,
            schema_error_count=error.error_count(),
            response_type=None,
        )

    if not isinstance(response, PlanResponse):
        return OutputEvaluation(
            json_valid=True,
            schema_valid=True,
            schema_error_count=0,
            response_type=response.response_type,
        )

    return OutputEvaluation(
        json_valid=True,
        schema_valid=True,
        schema_error_count=0,
        response_type=response.response_type,
        scope_violations=tuple(scope.plan_violations(response.plan)),
        time_coherence=check_time_coherence(response.plan, assumptions),
        order=check_exercise_order(response.plan),
        volume_sanity=check_volume_sanity(response.plan),
        exercise_uniqueness=check_exercise_uniqueness(response.plan),
        available_time_coherence=(
            check_available_time_coherence(response.plan, session_input, assumptions)
            if session_input is not None
            else None
        ),
        level_extremes=(
            check_level_extremes(response.plan, session_input)
            if session_input is not None
            else None
        ),
        injury_conflicts=(
            check_injury_conflicts(response.plan, session_input)
            if session_input is not None
            else None
        ),
    )


def _rate(hits: int, total: int) -> float | None:
    return hits / total if total else None


def summarize(evaluations: Sequence[OutputEvaluation]) -> EvaluationSummary:
    total = len(evaluations)
    plans = [item for item in evaluations if item.response_type == "plan"]
    time_checks = [item.time_coherence for item in plans]
    user_context_plans = [item for item in plans if item.available_time_coherence is not None]
    return EvaluationSummary(
        total=total,
        json_valid_rate=_rate(sum(item.json_valid for item in evaluations), total),
        schema_valid_rate=_rate(sum(item.schema_valid for item in evaluations), total),
        response_type_counts=dict(
            Counter(item.response_type or "invalid" for item in evaluations)
        ),
        plans=len(plans),
        scope_compliance_rate=_rate(sum(not item.scope_violations for item in plans), len(plans)),
        time_coherence_rate=_rate(sum(check.within_tolerance for check in time_checks), len(plans)),
        mean_absolute_time_error=(
            sum(abs(check.relative_error) for check in time_checks) / len(plans) if plans else None
        ),
        order_compliance_rate=_rate(sum(item.order.is_ordered for item in plans), len(plans)),
        volume_sanity_rate=_rate(
            sum(item.volume_sanity is not None and item.volume_sanity.is_sane for item in plans),
            len(plans),
        ),
        exercise_uniqueness_rate=_rate(
            sum(
                item.exercise_uniqueness is not None and item.exercise_uniqueness.is_unique
                for item in plans
            ),
            len(plans),
        ),
        available_time_coherence_rate=_rate(
            sum(
                item.available_time_coherence is not None
                and item.available_time_coherence.is_coherent
                for item in user_context_plans
            ),
            len(user_context_plans),
        ),
        level_compliance_rate=_rate(
            sum(
                item.level_extremes is not None and item.level_extremes.is_within_limits
                for item in user_context_plans
            ),
            len(user_context_plans),
        ),
        injury_compatibility_rate=_rate(
            sum(
                item.injury_conflicts is not None and item.injury_conflicts.is_compatible
                for item in user_context_plans
            ),
            len(user_context_plans),
        ),
    )
