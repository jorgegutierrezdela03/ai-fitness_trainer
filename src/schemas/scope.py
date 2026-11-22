"""Active training scope.

The schemas keep the full vocabulary of goals and modalities. This module decides which
of them are enabled. To extend the system, add a new scope and point ACTIVE_SCOPE to it:
the system prompt and the post-hoc scope checks both derive from it.

Scope checks only report violations. They never modify a profile or a model output.
"""

from dataclasses import dataclass

from .training_plan import ModalityType, TrainingPlanLLM
from .user_profile import TrainingGoal, TrainingStyle, UserProfile


@dataclass(frozen=True)
class TrainingScope:
    version: str
    goals: frozenset[TrainingGoal]
    training_styles: frozenset[TrainingStyle]
    main_block_modalities: frozenset[ModalityType]
    allow_additional_cardio: bool

    def profile_violations(self, profile: UserProfile) -> list[str]:
        violations = [
            f"Unsupported goal: {goal}" for goal in profile.primary_goals if goal not in self.goals
        ]
        style = profile.preferred_training_style
        if style is not None and style not in self.training_styles:
            violations.append(f"Unsupported training style: {style}")
        return violations

    def plan_violations(self, plan: TrainingPlanLLM) -> list[str]:
        violations = [
            f"Unsupported modality in main block: {exercise.name} ({exercise.modality})"
            for exercise in plan.main_block
            if exercise.modality not in self.main_block_modalities
        ]
        if plan.additional_cardio is not None and not self.allow_additional_cardio:
            violations.append("Additional cardio is not enabled in this scope.")
        return violations

    def to_prompt_section(self) -> str:
        cardio = "allowed" if self.allow_additional_cardio else "not allowed"
        return "\n".join(
            [
                f"- Supported training goals: {', '.join(sorted(self.goals))}.",
                "- Allowed main block modalities: "
                f"{', '.join(sorted(self.main_block_modalities))}.",
                f"- Additional cardio section: {cardio}.",
            ]
        )


PHASE_1_SCOPE = TrainingScope(
    version="phase1-strength-hypertrophy",
    goals=frozenset({"Strength", "Hypertrophy"}),
    training_styles=frozenset({"Resistance training", "No preference"}),
    main_block_modalities=frozenset({"Strength"}),
    allow_additional_cardio=False,
)

ACTIVE_SCOPE = PHASE_1_SCOPE
