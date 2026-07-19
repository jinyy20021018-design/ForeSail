"""Case-driven external-risk discovery connector.

Given a specific trade case (route, ports, commodity, Incoterm, parties, timing),
an LLM proposes external risk/news/policy items that could plausibly affect THIS
shipment — recent (already happening) or upcoming (scheduled/announced) — across
geopolitical, trade-policy, weather, market, operational and counterparty
dimensions. Because the items are generated from the case, their geography
(affected regions/ports/vessel) naturally matches the case, so the deterministic
relevance engine scores them against the shipment as usual.

The LLM only *surfaces candidate signals*; it never assigns a final relevance
score, exposure, status, or risk decision — those stay in the deterministic
engine. Runs through the shared llm_provider. No API key or a failed call
yields an empty list, never an error.
"""

import json
import os

from app.services import llm_provider

ALLOWED_EVENT_TYPES = [
    "GEOPOLITICAL", "TRADE_POLICY", "WEATHER", "SECURITY",
    "PORT_DISRUPTION", "ROUTE_DISRUPTION", "VESSEL_DELAY", "UNKNOWN",
]

# Map the discovered event type to a display source_type so LLM-found signals
# surface as POLICY / GEOPOLITICAL / WEATHER / PORT rather than defaulting to MOCK.
_SOURCE_TYPE_BY_EVENT = {
    "TRADE_POLICY": "POLICY",
    "GEOPOLITICAL": "GEOPOLITICAL",
    "SECURITY": "GEOPOLITICAL",
    "WEATHER": "WEATHER",
    "PORT_DISRUPTION": "PORT",
    "ROUTE_DISRUPTION": "NEWS",
    "VESSEL_DELAY": "NEWS",
    "UNKNOWN": "NEWS",
}


class LlmDiscoveryConnector:
    name = "llm_discovery_connector"

    def __init__(self) -> None:
        self.last_result: dict = {}

    def fetch_events(self, watch_profile: dict, case_id: str) -> list[dict]:
        if os.getenv("LLM_EVENT_DISCOVERY_ENABLED", "true").lower() != "true" or not llm_provider.api_key():
            self.last_result = {"enabled": False, "discovered": 0}
            return []

        from app.services.case_service import get_case
        try:
            case = get_case(case_id)
        except KeyError:
            self.last_result = {"enabled": True, "discovered": 0, "warnings": [f"Case not found: {case_id}"]}
            return []

        facts = {
            "vessel": case.get("vessel"),
            "route": case.get("route"),
            "port_of_loading": case.get("port_of_loading"),
            "port_of_discharge": case.get("port_of_discharge"),
            "final_destination": case.get("final_destination"),
            "commodity": case.get("commodity"),
            "incoterm": case.get("incoterm"),
            "etd": case.get("etd"),
            "eta": case.get("eta"),
            "latest_shipment_date": case.get("latest_shipment_date"),
        }
        try:
            content = llm_provider.chat_completion(
                messages=[
                    {"role": "system", "content": (
                        "You surface candidate external risk and policy signals for ONE cross-border shipment. "
                        "Return only JSON. Cover multiple dimensions across the items: geopolitical, trade_policy, "
                        "weather, security, port/route disruption, and market. Include both recent (already happening) "
                        "and upcoming (announced/scheduled) items. Ground each item in this shipment's own route, ports, "
                        "vessel, commodity and timing so it is checkable. Do NOT assign final relevance scores, exposures, "
                        "case status, or risk decisions — only identify plausible candidate signals."
                    )},
                    {"role": "user", "content": json.dumps({
                        "shipment": facts,
                        "allowed_event_types": ALLOWED_EVENT_TYPES,
                        "required_json_schema": {
                            "events": [{
                                "event_type": "TRADE_POLICY",
                                "title": "short headline",
                                "description": "1-2 sentences on what it is and why it may touch this shipment",
                                "affected_region": "a region/corridor on this route (e.g. Red Sea, Strait of Hormuz)",
                                "affected_ports": ["a port on this route"],
                                "severity": "LOW|MEDIUM|HIGH|CRITICAL",
                                "confidence": 0.6,
                                "timing": "recent|upcoming",
                                "category": "geopolitical|trade_policy|weather|market|operational|counterparty",
                            }],
                        },
                    }, ensure_ascii=True)},
                ],
                purpose="event_extraction",
                temperature=0.3,
                response_format={"type": "json_object"},
                timeout=int(os.getenv("LLM_EVENT_DISCOVERY_TIMEOUT_SECONDS", "30")),
            )
            items = json.loads(content).get("events")
        except Exception as error:
            self.last_result = {"enabled": True, "discovered": 0, "error": type(error).__name__}
            return []

        if not isinstance(items, list):
            self.last_result = {"enabled": True, "discovered": 0}
            return []

        events: list[dict] = []
        for index, item in enumerate(items[:8], start=1):
            if not isinstance(item, dict) or not item.get("title"):
                continue
            timing = str(item.get("timing") or "recent").lower()
            offset = 30 if timing == "upcoming" else -2
            etype = _event_type(item.get("event_type"))
            events.append({
                "event_id": f"EVT-LLM-{index:03d}",
                "title": "AI-inferred · " + str(item.get("title")),
                "type": etype,
                "source_type": _SOURCE_TYPE_BY_EVENT.get(etype, "NEWS"),
                "event_time_offset_days": offset,
                "affected_region": item.get("affected_region"),
                "affected_ports": item.get("affected_ports") if isinstance(item.get("affected_ports"), list) else [],
                "affected_vessel": facts.get("vessel"),
                "severity": str(item.get("severity") or "MEDIUM"),
                "confidence": _confidence(item.get("confidence")),
                "source": "ai_analyst_inference",
                "impact": "[AI-inferred signal — model-projected from this shipment's route, cargo and timing; not a verified news report] " + str(item.get("description") or item.get("title")),
                "discovery_category": item.get("category"),
                "discovery_timing": timing,
                "llm_inferred": True,
            })
        self.last_result = {"enabled": True, "discovered": len(events)}
        return events


def _event_type(value) -> str:
    text = str(value or "UNKNOWN").upper()
    return text if text in ALLOWED_EVENT_TYPES else "UNKNOWN"


def _confidence(value) -> float:
    try:
        return max(0.0, min(float(value), 1.0))
    except (TypeError, ValueError):
        return 0.6
