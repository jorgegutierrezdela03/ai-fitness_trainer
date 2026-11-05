"""Output schema draft. Final fields and bounds must be agreed in P1-06."""
from pydantic import BaseModel, ConfigDict, Field


class ExercisePrescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exercise_name: str = Field(min_length=2)
    sets: int = Field(ge=1, le=10)
    reps: str = Field(min_length=1, max_length=30)
    rir: int | None = Field(default=None, ge=0, le=5)
    rest_seconds: int | None = Field(default=None, ge=0, le=600)
    notes: str | None = None


class TrainingPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_name: str
    objective: str
    estimated_duration_minutes: int = Field(ge=1, le=240)
    exercises: list[ExercisePrescription] = Field(min_length=1)
    general_notes: list[str] = Field(default_factory=list)
