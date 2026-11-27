import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

import api.main as api_main
from baseline.generator import OllamaConfig, build_payload, generate_session
from schemas.user_profile import SessionGenerationInput

SAMPLE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "evaluation"
    / "examples"
    / "sample_user_input.json"
)
REFERRAL = {"response_type": "safety_referral", "reason": "warning_sign", "message": "Consulta."}


@pytest.fixture
def sample():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def ollama_client(content: str, status: int = 200) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"message": {"content": content}})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_payload_excludes_user_id_and_uses_schema(sample):
    payload = build_payload(SessionGenerationInput.model_validate(sample), OllamaConfig())
    assert "USR-001" not in payload["messages"][1]["content"]
    assert "oneOf" in payload["format"]
    assert payload["options"] == {"temperature": 0.0, "seed": 42}


def test_valid_output_is_parsed(sample):
    result = generate_session(
        SessionGenerationInput.model_validate(sample),
        OllamaConfig(),
        ollama_client(json.dumps(REFERRAL)),
    )
    assert result.is_valid
    assert result.response.response_type == "safety_referral"


def test_invalid_output_keeps_raw_text_and_errors(sample):
    raw = json.dumps({"response_type": "plan", "plan": {"title": "x"}})
    result = generate_session(
        SessionGenerationInput.model_validate(sample), OllamaConfig(), ollama_client(raw)
    )
    assert not result.is_valid
    assert result.raw_output == raw
    locations = [error["location"] for error in result.validation_errors]
    assert "plan.main_focus" in locations
    assert not any(location.startswith("plan.plan") for location in locations)


def test_options_follow_active_scope():
    body = TestClient(api_main.app).get("/api/options").json()
    assert body["goals"] == ["Hypertrophy", "Strength"]
    assert "Beginner" in body["experience_levels"]


def test_session_endpoint_returns_response(sample, monkeypatch):
    def fake_generate(session_input):
        return generate_session(session_input, OllamaConfig(), ollama_client(json.dumps(REFERRAL)))

    monkeypatch.setattr(api_main, "generate_session", fake_generate)
    body = TestClient(api_main.app).post("/api/sessions", json=sample).json()
    assert body["is_valid"] is True
    assert body["response"]["response_type"] == "safety_referral"
    assert body["metadata"]["model"] == "qwen2.5:7b"


def test_session_endpoint_rejects_invalid_input(sample):
    sample["user_profile"]["age"] = 15
    assert TestClient(api_main.app).post("/api/sessions", json=sample).status_code == 422


def test_session_endpoint_reports_unavailable_ollama(sample, monkeypatch):
    def failing_generate(session_input):
        return generate_session(session_input, OllamaConfig(), ollama_client("", status=500))

    monkeypatch.setattr(api_main, "generate_session", failing_generate)
    assert TestClient(api_main.app).post("/api/sessions", json=sample).status_code == 503
