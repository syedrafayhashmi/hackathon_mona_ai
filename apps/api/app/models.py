from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditEvent(BaseModel):
    stage: str
    title: str
    detail: str
    status: Literal["complete", "review", "blocked", "pending"] = "complete"
    at: str = Field(default_factory=now_iso)


class DataTable(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]


class WorkflowResult(BaseModel):
    summary: str
    table: DataTable
    evidence: list[str] = []
    warnings: list[str] = []
    review: dict[str, Any] = {}
    artifacts: list[str] = []


class AgentReview(BaseModel):
    decision: str
    owner: str
    risk: Literal["Low", "Medium", "High", "Critical"]


class AgentWorkflowOutput(BaseModel):
    summary: str
    rows: list[dict[str, Any]]
    evidence: list[str]
    warnings: list[str] = []
    review: AgentReview
    confidence: float = Field(ge=0.0, le=1.0)
    decision: str
    requires_approval: bool = True


class FileStatus(BaseModel):
    name: str
    status: Literal["pending", "processing", "completed", "failed"] = "pending"
    detail: str = ""


class RunRecord(BaseModel):
    id: str
    problem_id: str
    module_name: str
    fixture_id: str | None = None
    status: Literal["completed", "approved", "actioned", "blocked", "failed"] = "completed"
    confidence: float = 0.0
    source_mode: Literal["deterministic", "gemini", "fallback"] = "deterministic"
    agent_generated: bool = False
    model_usage: list[str] = []
    decision: str
    requires_approval: bool = True
    approved: bool = False
    created_at: str = Field(default_factory=now_iso)
    result: WorkflowResult
    audit_events: list[AuditEvent]
    file_statuses: list[FileStatus] = []


class ModuleDefinition(BaseModel):
    id: str
    name: str
    group: str
    description: str
    fixtures: list[dict[str, str]]
    action_label: str
