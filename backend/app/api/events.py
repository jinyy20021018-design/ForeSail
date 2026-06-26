from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.services.case_service import get_watch_profile
from app.services.document_service import get_confirmed_facts
from app.services.event_connectors.real_search_event_connector import RealSearchEventConnector
from app.services.event_deduplicator import deduplicate_events
from app.services.event_ingestion_service import (
    event_source_mode,
    fetch_events_for_case,
    list_external_events,
    list_external_events_for_run,
    save_external_events,
)
from app.services.event_normalizer import normalize_events
from app.services.mock_event_service import get_mock_events
from app.services.search_query_builder import build_external_event_queries
import os

router = APIRouter(tags=["events"])


@router.get("/api/events/mock")
def read_mock_events() -> list[dict]:
    return get_mock_events()


@router.get("/api/events/config")
def read_event_config() -> dict:
    mode = event_source_mode()
    return {
        "event_source_mode": mode,
        "connectors": _connectors_for_mode(mode),
        "real_search_enabled": os.getenv("REAL_SEARCH_ENABLED", "false").lower() == "true",
        "real_search_provider": os.getenv("REAL_SEARCH_PROVIDER", "RSS"),
        "real_search_lookback_days": _int_env("REAL_SEARCH_LOOKBACK_DAYS", 7),
        "configured_feeds_count": len([url for url in os.getenv("REAL_SEARCH_FEED_URLS", "").split(",") if url.strip()]),
        "use_llm_event_extraction": os.getenv("USE_LLM_EVENT_EXTRACTION", "false").lower() == "true",
    }


@router.get("/api/cases/{case_id}/external-events")
def read_external_events(
    case_id: str,
    source_type: str | None = None,
    event_type: str | None = None,
    classification: str | None = None,
    limit: int = Query(50, ge=1, le=200),
) -> list[dict]:
    events = list_external_events(case_id, source_type=source_type, event_type=event_type, limit=limit)
    if classification:
        # Classification is stored on relevance results, not event rows, in MVP 3.0.
        events = [event for event in events if str(event.get("classification", "")).lower() == classification.lower()]
    return events


@router.get("/api/cases/{case_id}/agent-runs/{agent_run_id}/external-events")
def read_agent_run_external_events(case_id: str, agent_run_id: str) -> list[dict]:
    return list_external_events_for_run(case_id, agent_run_id)


@router.post("/api/cases/{case_id}/external-events/fetch")
def fetch_external_events(case_id: str) -> dict:
    try:
        get_confirmed_facts(case_id)
        watch_profile = get_watch_profile(case_id)
    except KeyError:
        return JSONResponse(
            status_code=409,
            content={
                "error": "WATCH_PROFILE_REQUIRED",
                "message": "Confirmed case facts are required before fetching external events.",
            },
        )
    return fetch_events_for_case(case_id, watch_profile, persist=True)


@router.get("/api/cases/{case_id}/external-event-queries")
def read_external_event_queries(case_id: str):
    try:
        get_confirmed_facts(case_id)
        watch_profile = get_watch_profile(case_id)
    except KeyError:
        return JSONResponse(
            status_code=409,
            content={
                "error": "WATCH_PROFILE_REQUIRED",
                "message": "Confirmed case facts are required before generating external event search queries.",
            },
        )
    return {"case_id": case_id, "queries": build_external_event_queries(case_id, watch_profile)}


@router.post("/api/cases/{case_id}/external-events/search")
def search_external_events(case_id: str) -> dict:
    try:
        get_confirmed_facts(case_id)
        watch_profile = get_watch_profile(case_id)
    except KeyError:
        return JSONResponse(
            status_code=409,
            content={
                "error": "WATCH_PROFILE_REQUIRED",
                "message": "Confirmed case facts are required before searching external events.",
            },
        )
    connector = RealSearchEventConnector()
    connector_events = connector.fetch_events(watch_profile, case_id)
    normalized = normalize_events(connector_events, case_id, connector.name)
    deduped, stats = deduplicate_events(normalized)
    save_external_events(case_id, deduped)
    summary = connector.last_result or {}
    return {
        "case_id": case_id,
        "mode": "REAL_SEARCH",
        "queries_generated": summary.get("queries", []),
        "rss_items_fetched": summary.get("rss_items_fetched", 0),
        "rss_items_matched": summary.get("rss_items_matched", 0),
        "events_extracted": deduped,
        "events_extracted_count": len(deduped),
        "connector_errors": summary.get("connector_errors", []),
        "warnings": summary.get("warnings", []),
        "deduplication": stats,
    }


def _connectors_for_mode(mode: str) -> list[str]:
    if mode == "MOCK":
        return ["mock_event_connector"]
    if mode == "REAL":
        return ["weather_event_connector", "news_event_connector", "real_search_event_connector"]
    return ["mock_event_connector", "weather_event_connector", "news_event_connector", "real_search_event_connector"]


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default
