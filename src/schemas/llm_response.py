"""Top-level LLM output contract: a plan, or an explicit reason for not producing one."""

from typing import Annotated, Literal

from pydantic import Field, TypeAdapter

from .training_plan import StrictModel, TrainingPlanLLM

SafetyReason = Literal[
    "warning_sign",  # e.g., chest pain, fainting, dizziness, acute or worsening pain
    "medical_or_rehabilitation",  # diagnosis, treatment, or injury rehabilitation
    "excluded_population",  # e.g., minors or pregnancy
    "dangerous_request",  # extreme or manifestly unsafe training demand
]


class PlanResponse(StrictModel):
    response_type: Literal["plan"]
    plan: TrainingPlanLLM = Field(..., description="The generated training session.")


class ClarificationResponse(StrictModel):
    response_type: Literal["clarification"]
    questions: list[str] = Field(
        ..., min_length=1, max_length=3,
        description="Questions needed to generate an appropriate and safe session.",
    )


class SafetyReferralResponse(StrictModel):
    response_type: Literal["safety_referral"]
    reason: SafetyReason = Field(..., description="Category of the safety concern.")
    message: str = Field(
        ..., min_length=1,
        description="Brief message explaining why no session is generated and advising "
        "the user to consult a qualified professional. Must not diagnose or treat.",
    )


class OutOfScopeResponse(StrictModel):
    response_type: Literal["out_of_scope"]
    message: str = Field(
        ..., min_length=1,
        description="Brief message explaining that the request is outside the supported scope.",
    )


LLMResponse = Annotated[
    PlanResponse | ClarificationResponse | SafetyReferralResponse | OutOfScopeResponse,
    Field(discriminator="response_type"),
]

LLM_RESPONSE_ADAPTER: TypeAdapter[LLMResponse] = TypeAdapter(LLMResponse)
