import os

from app.services.event_connectors.mock_event_connector import MockEventConnector
from app.services.event_connectors.news_event_connector import NewsEventConnector
from app.services.event_connectors.real_search_event_connector import RealSearchEventConnector
from app.services.event_connectors.weather_event_connector import WeatherEventConnector
from app.services.event_deduplicator import deduplicate_events
from app.services.event_normalizer import normalize_events
from app.services.persistence_service import list_items, save_item

VALID_MODES = {"MOCK", "REAL", "HYBRID"}


def event_source_mode() -> str:
    mode = os.getenv("EVENT_SOURCE_MODE", "MOCK").upper()
    return mode if mode in VALID_MODES else "MOCK"


def fetch_events_for_case(case_id: str, watch_profile: dict, agent_run_id: str | None = None, persist: bool = False) -> dict:
    mode = event_source_mode()
    connectors = _connectors_for_mode(mode)
    raw_events: list[dict] = []
    normalized_events: list[dict] = []
    connectors_called: list[str] = []
    connector_errors: list[dict] = []
    connector_results: list[dict] = []

    for connector in connectors:
        connectors_called.append(connector.name)
        try:
            connector_events = connector.fetch_events(watch_profile, case_id)
            raw_events.extend(connector_events)
            normalized_events.extend(normalize_events(connector_events, case_id, connector.name))
            if getattr(connector, "last_result", None):
                connector_results.append({"connector": connector.name, **connector.last_result})
        except Exception as error:
            connector_errors.append({"connector": connector.name, "error": str(error)})

    deduped_events, dedup_stats = deduplicate_events(normalized_events)
    if persist:
        save_external_events(case_id, deduped_events, agent_run_id)

    return {
        "mode": mode,
        "connectors_called": connectors_called,
        "events_raw_count": len(raw_events),
        "events_normalized_count": len(normalized_events),
        "events_deduped_count": len(deduped_events),
        "events": deduped_events,
        "connector_errors": connector_errors,
        "connector_results": connector_results,
        "search_summary": _search_summary(connector_results),
        "deduplication": dedup_stats,
    }


def save_external_events(case_id: str, events: list[dict], agent_run_id: str | None = None) -> None:
    for event in events:
        item = dict(event)
        item["case_id"] = case_id
        item["agent_run_id"] = agent_run_id
        save_item("external_event", _event_key(case_id, item["event_id"], agent_run_id), item, case_id)


def list_external_events(case_id: str, source_type: str | None = None, event_type: str | None = None, limit: int | None = None) -> list[dict]:
    events = [event for event in list_items("external_event", case_id) if isinstance(event, dict)]
    if source_type:
        events = [event for event in events if str(event.get("source_type", "")).upper() == source_type.upper()]
    if event_type:
        events = [event for event in events if str(event.get("event_type", "")).upper() == event_type.upper()]
    events = sorted(events, key=lambda event: event.get("created_at") or "", reverse=True)
    return events[:limit] if limit else events


def list_external_events_for_run(case_id: str, agent_run_id: str) -> list[dict]:
    return [
        event
        for event in list_external_events(case_id)
        if event.get("agent_run_id") == agent_run_id
    ]


def _connectors_for_mode(mode: str):
    if mode == "MOCK":
        return [MockEventConnector()]
    if mode == "REAL":
        return [WeatherEventConnector(), NewsEventConnector(), RealSearchEventConnector()]
    return [MockEventConnector(), WeatherEventConnector(), NewsEventConnector(), RealSearchEventConnector()]


def _event_key(case_id: str, event_id: str, agent_run_id: str | None) -> str:
    return f"{case_id}:{agent_run_id or 'FETCH'}:{event_id}"


def _search_summary(connector_results: list[dict]) -> dict:
    summary = {
        "queries_generated": 0,
        "feeds_checked": 0,
        "rss_items_fetched": 0,
        "rss_items_matched": 0,
        "events_extracted": 0,
        "connector_errors": [],
        "warnings": [],
    }
    for result in connector_results:
        if result.get("connector") != "real_search_event_connector":
            continue
        for field in ["queries_generated", "feeds_checked", "rss_items_fetched", "rss_items_matched", "events_extracted"]:
            summary[field] += int(result.get(field) or 0)
        summary["connector_errors"].extend(result.get("connector_errors") or [])
        summary["warnings"].extend(result.get("warnings") or [])
    return summary
