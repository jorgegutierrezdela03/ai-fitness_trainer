"""Builds the system prompt from the versioned template and the active scope."""

from pathlib import Path

from schemas.scope import ACTIVE_SCOPE, TrainingScope

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "base_system_prompt.md"
SCOPE_PLACEHOLDER = "{{ACTIVE_SCOPE}}"


def render_system_prompt(scope: TrainingScope = ACTIVE_SCOPE) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.replace(SCOPE_PLACEHOLDER, scope.to_prompt_section())
