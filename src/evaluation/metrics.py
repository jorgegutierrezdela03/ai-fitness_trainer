"""Post-hoc metrics that need no benchmark labels, catalogue, or expert thresholds.

Every function only reads the model output. Raw text is never repaired, and invalid
outputs stay in the denominators so that failures cannot be excluded silently.
"""

import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import ValidationError

from schemas.llm_response import LLM_RESPONSE_ADAPTER, PlanResponse
from schemas.scope import ACTIVE_SCOPE, TrainingScope
from schemas.training_plan import ExerciseItem, TrainingPlanLLM

PRIORITY_RANK = {"Primary": 0, "Secondary": 1, "Accessory": 2}


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
class OutputEvaluation:
    json_valid: bool
    schema_valid: bool
    schema_error_count: int
    response_type: str | None
    scope_violations: tuple[str, ...] = ()
    time_coherence: TimeCoherence | None = None
    order: OrderCheck | None = None


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


def evaluate_output(
    raw_output: str,
    scope: TrainingScope = ACTIVE_SCOPE,
    assumptions: TimeAssumptions = DEFAULT_TIME_ASSUMPTIONS,
) -> OutputEvaluation:
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
    )


def _rate(hits: int, total: int) -> float | None:
    return hits / total if total else None


def summarize(evaluations: Sequence[OutputEvaluation]) -> EvaluationSummary:
    total = len(evaluations)
    plans = [item for item in evaluations if item.response_type == "plan"]
    time_checks = [item.time_coherence for item in plans]
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
    )
