"""HTTP API that exposes the baseline generator to the frontend."""

import os
from typing import Any, get_args

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from baseline.generator import OllamaConfig, OllamaUnavailableError, generate_session
from evaluation.metrics import evaluate_output
from schemas.llm_response import LLMResponse
from schemas.scope import ACTIVE_SCOPE
from schemas.user_profile import (
    BiologicalSex,
    BodyArea,
    EquipmentRestriction,
    ExperienceLevel,
    SessionGenerationInput,
)

load_dotenv()

app = FastAPI(title="FitEvidence AI", version="0.1.0")

# Next.js reaches the API through its own proxy. Expo web and native clients call it directly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8081").split(
        ","
    ),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class GenerationMetadata(BaseModel):
    model: str
    latency_seconds: float


class SessionResponse(BaseModel):
    is_valid: bool
    response: LLMResponse | None
    validation_errors: list[dict[str, Any]]
    raw_output: str
    metadata: GenerationMetadata
    scope_violations: list[str]
    time_coherence: dict[str, Any] | None


@app.get("/api/health")
def health() -> dict[str, Any]:
    config = OllamaConfig.from_env()
    try:
        tags = httpx.get(f"{config.base_url}/api/tags", timeout=3).json()
    except httpx.HTTPError:
        return {
            "api": "ok",
            "ollama": "unreachable",
            "model": config.model,
            "model_available": False,
        }
    names = {item.get("name") for item in tags.get("models", [])}
    return {
        "api": "ok",
        "ollama": "ok",
        "model": config.model,
        "model_available": config.model in names,
    }


@app.get("/api/options")
def options() -> dict[str, Any]:
    """Form choices. Goals come from the active scope, so the form follows ACTIVE_SCOPE."""
    return {
        "scope_version": ACTIVE_SCOPE.version,
        "goals": sorted(ACTIVE_SCOPE.goals),
        "training_styles": sorted(ACTIVE_SCOPE.training_styles),
        "experience_levels": list(get_args(ExperienceLevel)),
        "sexes": list(get_args(BiologicalSex)),
        "equipment": list(get_args(EquipmentRestriction)),
        "body_areas": list(get_args(BodyArea)),
    }


@app.post("/api/sessions", response_model=SessionResponse)
def create_session(payload: SessionGenerationInput) -> SessionResponse:
    try:
        result = generate_session(payload)
    except OllamaUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    evaluation = evaluate_output(result.raw_output)
    coherence = evaluation.time_coherence
    return SessionResponse(
        is_valid=result.is_valid,
        response=result.response,
        validation_errors=result.validation_errors,
        raw_output=result.raw_output,
        metadata=GenerationMetadata(
            model=result.model, latency_seconds=round(result.latency_seconds, 2)
        ),
        scope_violations=list(evaluation.scope_violations),
        time_coherence=coherence.__dict__ if coherence else None,
    )
