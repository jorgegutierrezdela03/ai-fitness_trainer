"""Output schema for the Training Plan LLM, including all the necessary fields and validations."""

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

# --- 1. CONTROLLED VOCABULARIES (Closed Options) ---
MuscleGroup = Literal[
    "Chest", "Back", "Quadriceps", "Hamstrings", 
    "Glutes", "Shoulders", "Biceps", "Triceps", "Calves", "Core", "Full_Body"
]
CardioIntensity = Literal["Low", "Moderate", "High"]
PriorityLevel = Literal["Primary", "Secondary", "Accessory"]
ModalityType = Literal["Strength", "Cardio", "Mobility"]


# --- 2. SECONDARY SECTIONS (Warm-up, Additional Cardio, Cool-down) ---
class WarmUpSection(BaseModel):
    general_activation: Optional[List[str]] = Field(
        None, description="Joint mobility exercises or light cardiovascular activity."
    )
    specific_warmup: Optional[List[str]] = Field(
        None, description="Specific activation exercises directly related to the main session movements."
    )
    warmup_sets: Optional[List[str]] = Field(
        None, description="Progressive preparation sets for the first main exercises, when appropriate."
    )

class AdditionalCardioSection(BaseModel):
    activity_type: str = Field(
        ..., description="Type of cardiovascular activity (e.g., Treadmill walk, Rowing, Stationary bike)."
    )
    duration_minutes: int = Field(
        ..., ge=1, le=120, description="Duration of the cardiovascular activity in minutes."
    )
    intensity: CardioIntensity = Field(
        ..., description="Target cardiovascular intensity level: Low, Moderate, or High."
    )
    instructions: Optional[str] = Field(
        None, description="Additional pacing or execution instructions, when appropriate."
    )

class CoolDownSection(BaseModel):
    exercises: List[str] = Field(
        ..., min_length=1, description="List of mobility or stretching exercises for recovery."
    )
    estimated_duration_minutes: Optional[int] = Field(
        None, ge=1, le=60, description="Estimated duration of the cool-down in minutes."
    )
    instructions: Optional[str] = Field(
        None, description="Additional breathing or relaxation guidance."
    )


# --- 3. CORE COMPONENT: EXERCISE ITEM ---
class ExerciseItem(BaseModel):
    name: str = Field(
        ..., description="Standard, descriptive name of the exercise."
    )
    modality: ModalityType = Field(
        ..., description="Exercise modality: Strength, Cardio, or Mobility."
    )
    priority: PriorityLevel = Field(
        ..., description="Importance within the session: Primary, Secondary, or Accessory."
    )
    
    # Muscle groups (Optional at field level because pure Cardio may not target a single muscle group)
    primary_muscle_group: Optional[MuscleGroup] = Field(
        None, description="Main muscle group targeted by the exercise, when applicable."
    )
    secondary_muscle_groups: Optional[List[MuscleGroup]] = Field(
        default_factory=list, description="Secondary or synergistic muscle groups involved."
    )
    
    # Modality-dependent training parameters
    sets: Optional[int] = Field(
        None, ge=1, le=15, description="Number of working sets (applicable to Strength or Mobility)."
    )
    reps: Optional[str] = Field(
        None, description="Target repetitions or repetition range, e.g., '8-10' or '12' (for Strength or Mobility)."
    )
    rest_seconds: Optional[int] = Field(
        None, ge=0, le=600, description="Rest time between sets in seconds (required for Strength)."
    )
    rpe: Optional[int] = Field(
        None, ge=1, le=10, description="Target intensity using Rate of Perceived Exertion from 1 to 10 (required for Strength)."
    )
    duration_minutes: Optional[int] = Field(
        None, ge=1, le=120, description="Duration in minutes (required for Cardio, optional for Mobility)."
    )
    cardio_intensity: Optional[CardioIntensity] = Field(
        None, description="Cardiovascular intensity level: Low, Moderate, or High (required for Cardio)."
    )
    
    # Technical instructions (Mandatory, 1 to 2 items as defined in P1-02.1)
    instructions: List[str] = Field(
        ..., min_length=1, max_length=2, 
        description="Brief, exercise-specific technical cues (maximum 2), adapted to user restrictions if applicable."
    )

    # Cross-field validator enforcing P1-02.1 modality rules (both required and forbidden fields)
    @model_validator(mode='after')
    def check_modality_parameters(self):
        if self.modality == "Strength":
            if None in (self.sets, self.reps, self.rest_seconds, self.rpe, self.primary_muscle_group):
                raise ValueError(
                    "Strength exercises require: sets, reps, rest_seconds, rpe, and primary_muscle_group."
                )
            if self.cardio_intensity is not None:
                raise ValueError("Strength exercises must not include cardio_intensity.")

        elif self.modality == "Cardio":
            if None in (self.duration_minutes, self.cardio_intensity):
                raise ValueError(
                    "Cardio exercises require: duration_minutes and cardio_intensity."
                )
            if any(x is not None for x in (self.sets, self.reps, self.rest_seconds, self.rpe)):
                raise ValueError(
                    "Cardio exercises must not include strength parameters (sets, reps, rest_seconds, rpe)."
                )

        elif self.modality == "Mobility":
            if self.duration_minutes is None and self.reps is None:
                raise ValueError(
                    "Mobility exercises require either duration_minutes or reps."
                )
            if any(x is not None for x in (self.rpe, self.cardio_intensity)):
                raise ValueError(
                    "Mobility exercises must not include rpe or cardio_intensity."
                )
        return self


# --- 4. MAIN LLM OUTPUT SCHEMA ---
class TrainingPlanLLM(BaseModel):
    title: str = Field(
        ..., description="Descriptive title of the training session."
    )
    main_focus: str = Field(
        ..., description="Primary physiological or anatomical focus of the session."
    )
    estimated_duration_minutes: int = Field(
        ..., ge=15, le=180, description="Estimated total session duration in minutes, aligned with user availability."
    )
    
    warm_up: Optional[WarmUpSection] = Field(
        None, description="Optional warm-up section depending on session requirements."
    )
    main_block: List[ExerciseItem] = Field(
        ..., min_length=1, max_length = 15, description="Ordered list of exercises composing the main training block."
    )
    additional_cardio: Optional[AdditionalCardioSection] = Field(
        None, description="Optional complementary cardiovascular training section."
    )
    cool_down: Optional[CoolDownSection] = Field(
        None, description="Optional cool-down and stretching section."
    )
    general_notes: Optional[str] = Field(
        None, description="Optional free-text notes for general execution, effort guidance, or progression reminders."
    )


# --- 5. COMPLETE SYSTEM OUTPUT SCHEMA (Backend-Enriched) ---
class SystemTrainingPlanOutput(TrainingPlanLLM):
    session_id: str = Field(
        ..., description="Unique session identifier generated by the Python backend."
    )
    user_id: str = Field(
        ..., description="User identifier managed by the Python backend."
    )
    generated_at: datetime = Field(
        default_factory=datetime.now, description="Generation timestamp managed by the Python backend."
    )
    exercise_ids_resolved: Optional[List[str]] = Field(
        None, description="Persistent exercise catalogue IDs resolved by the backend."
    )