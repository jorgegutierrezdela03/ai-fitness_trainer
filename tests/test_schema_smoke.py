from fitevidence.schemas.user_profile import BenchmarkCase


def test_example_benchmark_case_is_valid():
    case = BenchmarkCase.model_validate({
        "case_id": "FE-0001",
        "split": "development",
        "profile": {
            "age_years": 27,
            "experience_level": "beginner",
            "goal": "hypertrophy",
            "training_days_per_week": 3,
            "session_duration_minutes": 50,
            "equipment": ["full_gym"],
            "restrictions": [],
        },
        "request": "Quiero entrenar pecho y tríceps.",
        "expected": {
            "target_muscles": ["chest", "triceps"],
            "max_duration_minutes": 50,
            "must_respect_experience_level": True,
            "clarification_expected": False,
            "safety_route_expected": False,
        },
        "tags": ["beginner", "hypertrophy", "normal"],
    })
    assert case.case_id == "FE-0001"
