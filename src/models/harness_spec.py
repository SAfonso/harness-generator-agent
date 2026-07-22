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


# --- Modelos runtime del harness generado (v2) ---------------------------
# No viajan por este pipeline (intake→analysis→generator→validator): describen
# artefactos del harness YA generado en ejecución. Ver specs/models.md.

class LedgerDecision(BaseModel):
    id: str
    date: str
    summary: str
    scope: list[str]
    task_id: int | None = None


class IntegrationReport(BaseModel):
    task_id: int
    pushed: bool
    branch: str | None = None
    pr_url: str | None = None
    ci_status: Literal["pending", "passed", "failed"] | None = None
    merge_status: Literal["pending", "merged", "conflict", "failed"] | None = None
    failure_context: str | None = None


class TaskCloseOut(BaseModel):
    task_id: int
    status: Literal["integrated", "escalated"]
    summary: str
    decisions: list[LedgerDecision] = []
    commit: str | None = None
    pr_url: str | None = None
    attempts: int


class ContextPackage(BaseModel):
    task_id: int
    task_spec: dict
    relevant_decisions: list[LedgerDecision]
    relevant_task_summaries: list[TaskCloseOut]
    acceptance_criteria: list[str]


class Ledger(BaseModel):
    decisions: list[LedgerDecision] = []
    tasks: list[TaskCloseOut] = []