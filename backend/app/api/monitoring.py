from fastapi import APIRouter, HTTPException

from app.agents.monitoring_agent import MonitoringAgent
from app.services.agent_run_service import get_agent_run, get_agent_run_trace, get_agent_runs
from app.services.case_service import get_timeline
from app.services.monitoring_service import run_monitoring_cycle

router = APIRouter(prefix="/api/cases", tags=["monitoring"])
monitoring_agent = MonitoringAgent()


@router.post("/{case_id}/monitor")
def monitor_case(case_id: str) -> dict:
    try:
        result = run_monitoring_cycle(case_id)
        result["status_timeline"] = get_timeline(case_id)
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}") from None


@router.post("/{case_id}/agent-run")
def run_agent_monitoring_cycle(case_id: str) -> dict:
    try:
        return monitoring_agent.run_monitoring_cycle(case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}") from None
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/{case_id}/agent-runs")
def read_agent_runs(case_id: str) -> list[dict]:
    try:
        return get_agent_runs(case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}") from None


@router.get("/{case_id}/agent-runs/{agent_run_id}")
def read_agent_run(case_id: str, agent_run_id: str) -> dict:
    try:
        return get_agent_run(case_id, agent_run_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Agent run not found: {agent_run_id}") from None


@router.get("/{case_id}/agent-runs/{agent_run_id}/trace")
def read_agent_run_trace(case_id: str, agent_run_id: str) -> list[dict]:
    try:
        return get_agent_run_trace(case_id, agent_run_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Agent run not found: {agent_run_id}") from None
