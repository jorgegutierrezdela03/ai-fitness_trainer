import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from baseline.prompt import SCOPE_PLACEHOLDER, render_system_prompt
from schemas.llm_response import (
    LLM_RESPONSE_ADAPTER,
    ClarificationResponse,
    OutOfScopeResponse,
    PlanResponse,
    SafetyReferralResponse,
)
from schemas.scope import ACTIVE_SCOPE, PHASE_1_SCOPE, TrainingScope
from schemas.training_plan import ExerciseItem, SystemTrainingPlanOutput, TrainingPlanLLM
from schemas.user_profile import SessionGenerationInput

EXAMPLES = Path(__file__).resolve().parents[1] / "data" / "evaluation" / "examples"
BACKEND_FIELDS = ("session_id", "user_id", "generated_at", "exercise_ids_resolved")


def load(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


@pytest.fixture
def system_plan():
    return load("training_plan_schema_validation.json")


@pytest.fixture
def llm_plan(system_plan):
    return {key: value for key, value in system_plan.items() if key not in BACKEND_FIELDS}


@pytest.fixture
def profile():
    return SessionGenerationInput.model_validate(load("sample_user_input.json")).user_profile


def strength(**overrides):
    fields = {
        "name": "Bench Press",
        "modality": "Strength",
        "priority": "Primary",
        "primary_muscle_group": "Chest",
        "sets": 3,
        "reps": "8-10",
        "rest_seconds": 90,
        "rpe": 8,
        "instructions": ["Control the descent."],
    }
    return {**fields, **overrides}


def test_examples_are_valid(system_plan, llm_plan):
    SystemTrainingPlanOutput.model_validate(system_plan)
    TrainingPlanLLM.model_validate(llm_plan)


def test_llm_plan_rejects_backend_metadata(llm_plan):
    with pytest.raises(ValidationError):
        TrainingPlanLLM.model_validate({**llm_plan, "session_id": "SES-1"})


@pytest.mark.parametrize("reps", ["12", "8-10"])
def test_valid_reps(reps):
    assert ExerciseItem(**strength(reps=reps)).reps == reps


@pytest.mark.parametrize("reps", ["banana", "-5", "0", "10-8", "8-8", "8-", ""])
def test_invalid_reps(reps):
    with pytest.raises(ValidationError):
        ExerciseItem(**strength(reps=reps))


def test_strength_rejects_duration():
    with pytest.raises(ValidationError):
        ExerciseItem(**strength(duration_minutes=30))


@pytest.mark.parametrize(
    "payload, expected",
    [
        ({"response_type": "clarification", "questions": ["¿Cuánto tiempo tienes?"]},
         ClarificationResponse),
        ({"response_type": "safety_referral", "reason": "warning_sign", "message": "Consulta."},
         SafetyReferralResponse),
        ({"response_type": "out_of_scope", "message": "Fuera de alcance."}, OutOfScopeResponse),
    ],
)
def test_non_plan_responses(payload, expected):
    assert isinstance(LLM_RESPONSE_ADAPTER.validate_python(payload), expected)


def test_plan_response(llm_plan):
    response = LLM_RESPONSE_ADAPTER.validate_python({"response_type": "plan", "plan": llm_plan})
    assert isinstance(response, PlanResponse)


@pytest.mark.parametrize(
    "payload",
    [
        {"response_type": "unknown"},
        {"response_type": "clarification", "questions": []},
        {"response_type": "clarification", "questions": ["a", "b", "c", "d"]},
        {"response_type": "safety_referral", "reason": "other", "message": "x"},
        {"response_type": "out_of_scope", "message": "x", "plan": {}},
    ],
)
def test_invalid_responses(payload):
    with pytest.raises(ValidationError):
        LLM_RESPONSE_ADAPTER.validate_python(payload)


def test_response_json_schema_can_be_generated():
    schema = LLM_RESPONSE_ADAPTER.json_schema()
    assert len(schema["oneOf"]) == 4


def test_active_scope_is_phase_1():
    assert ACTIVE_SCOPE is PHASE_1_SCOPE
    assert ACTIVE_SCOPE.goals == {"Strength", "Hypertrophy"}


def test_phase_1_accepts_sample_profile_and_plan(profile, llm_plan):
    assert PHASE_1_SCOPE.profile_violations(profile) == []
    assert PHASE_1_SCOPE.plan_violations(TrainingPlanLLM.model_validate(llm_plan)) == []


def test_future_goals_stay_valid_in_schema_but_flagged_by_scope(profile):
    extended = profile.model_copy(update={"primary_goals": ["Hypertrophy", "Fat loss"]})
    assert PHASE_1_SCOPE.profile_violations(extended) == ["Unsupported goal: Fat loss"]


def test_phase_1_flags_cardio_without_modifying_plan(llm_plan):
    data = copy.deepcopy(llm_plan)
    data["additional_cardio"] = {"activity_type": "Bike", "duration_minutes": 10,
                                 "intensity": "Low"}
    data["main_block"].append({
        "name": "Treadmill", "modality": "Cardio", "priority": "Accessory",
        "duration_minutes": 10, "cardio_intensity": "Low", "instructions": ["Keep pace."],
    })
    plan = TrainingPlanLLM.model_validate(data)
    before = plan.model_dump()
    assert len(PHASE_1_SCOPE.plan_violations(plan)) == 2
    assert plan.model_dump() == before


def test_new_scope_enables_goals_without_schema_changes(profile, llm_plan):
    future = TrainingScope(
        version="future",
        goals=PHASE_1_SCOPE.goals | {"Fat loss"},
        training_styles=PHASE_1_SCOPE.training_styles,
        main_block_modalities=frozenset({"Strength", "Cardio"}),
        allow_additional_cardio=True,
    )
    extended = profile.model_copy(update={"primary_goals": ["Fat loss"]})
    assert future.profile_violations(extended) == []
    assert "Fat loss" in render_system_prompt(future)


def test_prompt_renders_active_scope():
    prompt = render_system_prompt()
    assert SCOPE_PLACEHOLDER not in prompt
    assert "Supported training goals: Hypertrophy, Strength." in prompt
    assert "Additional cardio section: not allowed." in prompt
    for response_type in ("safety_referral", "out_of_scope", "clarification", "`plan`"):
        assert response_type in prompt
