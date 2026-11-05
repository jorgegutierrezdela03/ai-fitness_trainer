"""Pydantic models for benchmark cases. Extend after the schema is approved."""
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class UserProfile(BaseModel):
    model_config = ConfigDict(extra="allow")

    age_years: int = Field(ge=18, le=100)
    experience_level: Literal["beginner", "intermediate", "advanced"]
    goal: Literal["hypertrophy", "strength", "general_fitness"]
    training_days_per_week: int | None = Field(default=None, ge=1, le=7)
    session_duration_minutes: int = Field(ge=10, le=180)
    equipment: list[str]
    restrictions: list[str] = Field(default_factory=list)


class ExpectedConstraints(BaseModel):
    model_config = ConfigDict(extra="allow")

    target_muscles: list[str] = Field(default_factory=list)
    max_duration_minutes: int | None = Field(default=None, ge=10, le=180)
    must_respect_experience_level: bool = True
    clarification_expected: bool = False
    safety_route_expected: bool = False


class BenchmarkCase(BaseModel):
    case_id: str
    split: Literal["development", "test"]
    profile: UserProfile
    request: str = Field(min_length=3)
    expected: ExpectedConstraints
    tags: list[str] = Field(default_factory=list)
