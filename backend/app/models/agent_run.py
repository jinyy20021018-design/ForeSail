from dataclasses import dataclass
from typing import Any


@dataclass
class AgentRunTraceStep:
    step: int
    name: str
    status: str
    description: str
    tool_or_service: str
    output_summary: str


@dataclass
class AgentRunResult:
    agent_run_id: str
    case_id: str
    status_before: str
    status_after: str
    summary: str
    trace: list[AgentRunTraceStep]
    events_scanned: int
    relevant_count: int
    watch_count: int
    irrelevant_count: int
    case: dict[str, Any]
    watch_profile: dict[str, Any]
    relevance_results: list[dict[str, Any]]
    risk_summary: dict[str, Any]
    actions: list[dict[str, Any]]
    status_timeline: list[dict[str, Any]]
