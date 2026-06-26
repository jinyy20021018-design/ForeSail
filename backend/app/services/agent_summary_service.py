import json
import os
from pathlib import Path
import urllib.request


def generate_agent_summary_result(
    *,
    case: dict,
    status_before: str,
    status_after: str,
    relevance_results: list[dict],
    risk_summary: dict,
    actions: list[dict],
    obligations: list[dict] | None = None,
    information_gaps: list[dict] | None = None,
    action_drafts: list[dict] | None = None,
) -> dict:
    _load_local_env()
    deterministic_summary = _deterministic_summary(
        case=case,
        status_before=status_before,
        status_after=status_after,
        relevance_results=relevance_results,
        risk_summary=risk_summary,
        actions=actions,
        obligations=obligations or [],
        information_gaps=information_gaps or [],
        action_drafts=action_drafts or [],
    )

    api_key = os.getenv("OPENAI_API_KEY")
    llm_required = _truthy(os.getenv("REQUIRE_LLM_AGENT"))
    llm_requested = llm_required or _truthy(os.getenv("USE_LLM_SUMMARY")) or bool(api_key)

    if not llm_requested:
        return {
            "summary": deterministic_summary,
            "summary_source": "deterministic",
            "llm_enabled": False,
            "llm_required": False,
        }

    if not api_key:
        if llm_required:
            raise RuntimeError("LLM Agent is required, but OPENAI_API_KEY is not configured.")
        return {
            "summary": deterministic_summary,
            "summary_source": "deterministic_fallback",
            "llm_enabled": False,
            "llm_required": False,
        }

    try:
        summary = _openai_summary(
            api_key=api_key,
            fallback=deterministic_summary,
            case=case,
            status_before=status_before,
            status_after=status_after,
            relevance_results=relevance_results,
            risk_summary=risk_summary,
            actions=actions,
            obligations=obligations or [],
            information_gaps=information_gaps or [],
            action_drafts=action_drafts or [],
        )
        return {
            "summary": summary,
            "summary_source": "llm",
            "llm_enabled": True,
            "llm_required": llm_required,
        }
    except Exception as error:
        if llm_required:
            raise RuntimeError("LLM Agent summary failed while REQUIRE_LLM_AGENT=true.") from error
        return {
            "summary": deterministic_summary,
            "summary_source": "deterministic_fallback",
            "llm_enabled": False,
            "llm_required": False,
        }


def generate_agent_summary(
    *,
    case: dict,
    status_before: str,
    status_after: str,
    relevance_results: list[dict],
    risk_summary: dict,
    actions: list[dict],
    obligations: list[dict] | None = None,
    information_gaps: list[dict] | None = None,
    action_drafts: list[dict] | None = None,
) -> str:
    return generate_agent_summary_result(
        case=case,
        status_before=status_before,
        status_after=status_after,
        relevance_results=relevance_results,
        risk_summary=risk_summary,
        actions=actions,
        obligations=obligations or [],
        information_gaps=information_gaps or [],
        action_drafts=action_drafts or [],
    )["summary"]


def _deterministic_summary(
    *,
    case: dict,
    status_before: str,
    status_after: str,
    relevance_results: list[dict],
    risk_summary: dict,
    actions: list[dict],
    obligations: list[dict],
    information_gaps: list[dict],
    action_drafts: list[dict],
) -> str:
    relevant = [result for result in relevance_results if result["classification"] == "Relevant"]
    watch = [result for result in relevance_results if result["classification"] == "Watch"]
    irrelevant = [result for result in relevance_results if result["classification"] == "Irrelevant"]
    exposure_categories = [exposure["category"] for exposure in risk_summary.get("exposures", [])]

    trigger_text = ", ".join(risk_summary.get("trigger_events", [])) or "no trigger events"
    watch_text = ", ".join(risk_summary.get("watch_events_considered", [])) or "no watch events"
    action_count = len(actions)
    obligations_at_risk = [obligation for obligation in obligations if "risk" in obligation.get("current_assessment", "").lower()]

    return (
        f"Agent scanned {len(relevance_results)} external events for {case['case_id']}. "
        f"{len(relevant)} events were classified as Relevant, {len(watch)} as Watch, "
        f"and {len(irrelevant)} as Irrelevant. "
        f"The case moved from {status_before} to {status_after}. "
        f"Trigger events: {trigger_text}. Watch events considered: {watch_text}. "
        f"{action_count} recommended actions were generated for "
        f"{', '.join(exposure_categories) if exposure_categories else 'no triggered exposure categories'}. "
        f"{len(obligations_at_risk)} obligations are at risk, {len(information_gaps)} information gaps were detected, "
        f"and {len(action_drafts)} action drafts were prepared for user review."
    )


def _openai_summary(
    *,
    api_key: str,
    fallback: str,
    case: dict,
    status_before: str,
    status_after: str,
    relevance_results: list[dict],
    risk_summary: dict,
    actions: list[dict],
    obligations: list[dict],
    information_gaps: list[dict],
    action_drafts: list[dict],
) -> str:
    model = os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4.1-mini")
    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": (
                    "Write a concise user-facing agent run summary. Do not make new scoring, "
                    "classification, exposure, status, date, or action decisions. Use only the supplied facts."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "case_id": case["case_id"],
                        "vessel": case["vessel"],
                        "route": case["route"],
                        "status_before": status_before,
                        "status_after": status_after,
                        "relevance_results": [
                            {
                                "event_id": result["event_id"],
                                "classification": result["classification"],
                                "mapped_exposures": result["mapped_exposures"],
                            }
                            for result in relevance_results
                        ],
                        "risk_summary": risk_summary,
                        "obligations_at_risk": [
                            obligation
                            for obligation in obligations
                            if "risk" in obligation.get("current_assessment", "").lower()
                        ],
                        "information_gap_count": len(information_gaps),
                        "action_draft_count": len(action_drafts),
                        "action_count": len(actions),
                    },
                    ensure_ascii=True,
                ),
            },
        ],
    }

    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        data = json.loads(response.read().decode("utf-8"))

    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    return fallback


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
