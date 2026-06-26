from datetime import date

from app.services.persistence_service import list_item_records, list_items, load_item


def list_case_summaries() -> list[dict]:
    summaries = []
    for record in list_item_records("case"):
        case = record["payload"]
        case_id = case["case_id"]
        confirmed_facts = load_item("confirmed_facts", case_id) or {}
        obligations = _case_collection("obligations", case_id)
        gaps = _case_collection("information_gaps", case_id)
        actions = _case_collection("actions", case_id)
        conflicts = _case_collection("field_conflicts", case_id)
        runs = _case_collection("agent_run", case_id)

        open_conflicts = [conflict for conflict in conflicts if _is_open(conflict.get("status"))]
        high_conflicts = [
            conflict
            for conflict in open_conflicts
            if str(conflict.get("severity", "")).lower() == "high"
        ]
        open_gaps = [gap for gap in gaps if _is_open(gap.get("status"))]
        open_actions = [action for action in actions if _is_open_action(action.get("status"))]
        latest_run = _latest_agent_run(runs)
        next_deadline = _next_deadline(obligations, confirmed_facts, case)
        risk_level = _risk_level(case.get("status"), obligations, len(open_gaps), len(high_conflicts))

        summaries.append({
            "case_id": case_id,
            "vessel": confirmed_facts.get("vessel") or case.get("vessel"),
            "route": confirmed_facts.get("route") or case.get("route"),
            "port_of_loading": confirmed_facts.get("port_of_loading") or case.get("port_of_loading"),
            "port_of_discharge": confirmed_facts.get("port_of_discharge") or case.get("port_of_discharge"),
            "final_destination": confirmed_facts.get("final_destination") or case.get("final_destination"),
            "status": case.get("status"),
            "risk_level": risk_level,
            "next_deadline": next_deadline,
            "open_actions_count": len(open_actions),
            "information_gaps_count": len(open_gaps),
            "open_conflicts_count": len(open_conflicts),
            "high_conflicts_count": len(high_conflicts),
            "last_agent_run_at": _run_time(latest_run) if latest_run else None,
            "last_agent_run_id": latest_run.get("agent_run_id") if latest_run else None,
            "owner": case.get("owner") or "Trade Ops",
            "updated_at": record.get("updated_at"),
        })
    return summaries


def _risk_level(status: str | None, obligations: list[dict], information_gaps_count: int, high_conflicts_count: int) -> str:
    if high_conflicts_count > 0:
        return "High"
    if any(
        _is_open(obligation.get("status")) and str(obligation.get("severity", "")).lower() == "high"
        for obligation in obligations
    ):
        return "High"
    if status in {"ACTION_REQUIRED", "AT_RISK"}:
        return "High"
    if information_gaps_count > 0:
        return "Medium"
    return "Low"


def _case_collection(namespace: str, case_id: str) -> list[dict]:
    stored = load_item(namespace, case_id)
    if isinstance(stored, list):
        return [item for item in stored if isinstance(item, dict)]
    records = list_items(namespace, case_id)
    flattened: list[dict] = []
    for record in records:
        if isinstance(record, list):
            flattened.extend(item for item in record if isinstance(item, dict))
        elif isinstance(record, dict):
            flattened.append(record)
    return flattened


def _next_deadline(obligations: list[dict], confirmed_facts: dict, case: dict) -> dict | None:
    open_obligations = [
        obligation
        for obligation in obligations
        if _is_open(obligation.get("status")) and _parse_date(obligation.get("deadline_date"))
    ]
    if open_obligations:
        nearest = min(open_obligations, key=lambda obligation: _parse_date(obligation.get("deadline_date")) or date.max)
        return {"label": nearest.get("name") or "Obligation deadline", "date": nearest.get("deadline_date")}

    latest = confirmed_facts.get("latest_shipment_date") or case.get("latest_shipment_date")
    if latest:
        return {"label": "Latest shipment", "date": latest}
    return None


def _latest_agent_run(runs: list[dict]) -> dict | None:
    if not runs:
        return None
    return max(runs, key=lambda run: _run_time(run) or "")


def _run_time(run: dict) -> str | None:
    return run.get("completed_at") or run.get("started_at")


def _is_open(status: str | None) -> bool:
    return str(status or "").upper() == "OPEN"


def _is_open_action(status: str | None) -> bool:
    return str(status or "").upper() not in {"", "DONE", "COMPLETED", "CLOSED", "ARCHIVED"}


def _parse_date(value) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
