from pydantic import BaseModel
from typing import Literal


class AgentRole(BaseModel):
    name: str
    mode: str
    scope: str
    tools: list[str]

class LLMConfig(BaseModel):
    strategy: Literal["same", "recommended", "custom"]
    default_model: str | None = None
    per_agent: dict[str, str] = {}

class HarnessSpec(BaseModel):
    # Recogido por intake_agent
    project_type: Literal["data_pipeline", "api", "web", "agent", "cli", "other"]
    description: str
    stack: list[str]
    data_sources: list[str]
    constraints: list[str]
    acceptance_criteria: list[str]
    deliverable: str
    time_available: str

    # Decidido por analysis_agent
    agent_roles: list[AgentRole] = []
    harness_complexity: Literal["simple", "standard", "complex"] | None = None
    rules: list[str] = []

    # Metadatos
    mode: Literal["EJECUTOR", "PROFESOR"]
    llm_config: LLMConfig
    generated_at: str = ""


class IntakeResult(BaseModel):
    spec: HarnessSpec | None = None
    status: Literal["complete", "needs_input"]
    questions: list[str] = []