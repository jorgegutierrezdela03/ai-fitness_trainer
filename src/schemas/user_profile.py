"""User profile schema with data types, controlled vocabularies, and conditional validation logic for fitness session generation."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

# --- 1. CONTROLLED VOCABULARIES (Predefined Options) ---
ExperienceLevel = Literal["Beginner", "Intermediate", "Advanced"]

TrainingGoal = Literal[
    "Strength", "Hypertrophy", "Fat loss", 
    "Cardiovascular fitness", "Muscular endurance", "General fitness"
]

BiologicalSex = Literal["Male", "Female", "Other", "Prefer not to say"]


TrainingStyle = Literal[
    "Resistance training", 
    "Cardiovascular training", 
    "Combined resistance and cardiovascular training", 
    "No preference"
]

EquipmentRestriction = Literal[
    "Dumbbells", "Barbells", "Resistance machines", 
    "Cable machines", "Cardiovascular equipment", "Other"
]

BodyArea = Literal[
    "Shoulder", "Elbow", "Wrist", "Back", "Hip", "Knee", "Ankle", "Other"
]


# --- 2. PHYSICAL LIMITATIONS SUB-SCHEMA ---
class PhysicalLimitations(BaseModel):
    has_limitations: bool = Field(
        ..., description="Required Yes/No (True/False) indicating if the user has physical limitations."
    )
    affected_areas: Optional[List[BodyArea]] = Field(
        default_factory=list, 
        description="Affected body areas. Required if has_limitations is True."
    )
    description: Optional[str] = Field(
        None, max_length=300,
        description="Optional brief free-text description of the physical limitation."
    )

    @model_validator(mode='after')
    def check_conditional_limitations(self):
        if self.has_limitations and not self.affected_areas:
            raise ValueError(
                "If 'has_limitations' is True, at least one 'affected_areas' item must be selected."
            )
        if not self.has_limitations and (self.affected_areas or self.description):
            raise ValueError(
                "If 'has_limitations' is False, 'affected_areas' and 'description' must be empty."
            )
        return self


# --- 3. MAIN USER PROFILE SCHEMA (P1-01.2) ---
class UserProfile(BaseModel):
    # System identifier (optional for raw LLM prompt, useful for dataset tracking)
    user_id: Optional[str] = Field(
        None, description="Unique identifier for synthetic or real user profiles."
    )

    # 1. Basic Information
    age: int = Field(
        ..., ge=18, le=100, description="User age in years (must be 18 or older)."
    )
    sex: Optional[BiologicalSex] = Field(
        None, description="Optional biological sex or gender identity."
    )
    height_cm: Optional[float] = Field(
        None, ge=100.0, le=250.0, description="Optional height in centimeters."
    )
    weight_kg: Optional[float] = Field(
        None, ge=30.0, le=300.0, description="Optional weight in kilograms."
    )

    # 2. Training Experience
    experience_level: ExperienceLevel = Field(
        ..., description="Training experience level: Beginner, Intermediate, or Advanced."
    )

    # 3. Training Goals (1 to 2 goals)
    primary_goals: List[TrainingGoal] = Field(
        ..., min_length=1, max_length=2, 
        description="Up to two primary training objectives."
    )

    # 4. Training Availability
    available_days_per_week: int = Field(
        ..., ge=1, le=7, description="Available training days per week (1 to 7)."
    )
    session_duration_minutes: int = Field(
        ..., ge=15, le=180, description="Available duration per session in minutes."
    )
    
    # 5. Training Preferences and Restrictions
    exercises_to_avoid: Optional[List[str]] = Field(
        None, description="Optional list of specific exercises the user prefers to avoid."
    )
    equipment_limitations: Optional[List[EquipmentRestriction]] = Field(
        None, description="Optional equipment that is unavailable or avoided by the user."
    )
    preferred_training_style: Optional[TrainingStyle] = Field(
        None, description="Optional preferred training style."
    )

    # 6. Physical Limitations
    physical_limitations: PhysicalLimitations = Field(
        ..., description="Mandatory physical limitations status and conditional details."
    )

    @model_validator(mode='after')
    def check_unique_goals(self):
        if len(self.primary_goals) != len(set(self.primary_goals)):
            raise ValueError("Selected 'primary_goals' must be unique (no duplicates).")
        return self


# --- 4. COMPLETE LLM INPUT PAYLOAD (Profile + Natural Language Request) ---
class SessionGenerationInput(BaseModel):
    user_profile: UserProfile = Field(
        ..., description="Structured objective and preference data of the user."
    )
    session_request: str = Field(
        ..., min_length=3, max_length=500,
        description="Natural language request for the specific session (e.g., 'I want an upper body workout focused on back')."
    )
    conversation_context: Optional[str] = Field(
        None, max_length=1000,
        description="Optional prior conversation context or history to help interpret follow-up requests."
    )
