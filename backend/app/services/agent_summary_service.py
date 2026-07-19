import json
import os
from pathlib import Path
import urllib.error
import urllib.request

from app.services import llm_provider


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

    api_key = llm_provider.api_key()
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
            return {
                "summary": deterministic_summary,
                "summary_source": "deterministic_fallback",
                "llm_enabled": False,
                "llm_required": True,
                "summary_warning": f"LLM required but no {llm_provider.provider_label()} API key is configured; used deterministic summary.",
            }
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
            return {
                "summary": deterministic_summary,
                "summary_source": "deterministic_fallback",
                "llm_enabled": False,
                "llm_required": True,
                "summary_warning": (
                    "LLM Agent summary failed while REQUIRE_LLM_AGENT=true "
                    f"({_format_openai_error(error)}); used deterministic summary."
                ),
            }
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
    user_content = json.dumps(
        {
            "case_id": case["case_id"],
            "vessel": case["vessel"],
            "route": case["route"],
            "status_before": status_before,
            "status_after": status_after,
            "relevance_results": [
                {
                    "event_id": result.get("event_id"),
                    "classification": result.get("classification"),
                    "mapped_exposures": result.get("mapped_exposures", []),
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
    )
    messages = [
        {
            "role": "system",
            "content": (
                "Write a concise user-facing agent run summary. Do not make new scoring, "
                "classification, exposure, status, date, or action decisions. Use only the supplied facts."
            ),
        },
        {"role": "user", "content": user_content},
    ]
    timeout_seconds = int(os.getenv("OPENAI_SUMMARY_TIMEOUT_SECONDS", "60"))
    content = llm_provider.chat_completion(
        messages=messages,
        purpose="summary",
        temperature=0.2,
        timeout=timeout_seconds,
    )
    if isinstance(content, str) and content.strip():
        return content.strip()

    return fallback


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _format_openai_error(error: Exception) -> str:
    if isinstance(error, urllib.error.HTTPError):
        try:
            body = error.read().decode("utf-8")
            parsed = json.loads(body)
            message = parsed.get("error", {}).get("message")
            if message:
                return f"HTTP {error.code}: {message}"
        except Exception:
            pass
        return f"HTTP {error.code}: {error.reason}"
    return str(error)


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    refresh_keys = {
        "OPENAI_SUMMARY_MODEL",
        "OPENAI_SUMMARY_TIMEOUT_SECONDS",
    }
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key not in refresh_keys:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")
