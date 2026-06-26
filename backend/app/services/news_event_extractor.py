import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta


def extract_event_from_news_item(item: dict, watch_profile: dict) -> dict | None:
    if os.getenv("USE_LLM_EVENT_EXTRACTION", "false").lower() == "true" and os.getenv("OPENAI_API_KEY"):
        event = _try_llm_extract(item, watch_profile)
        if event:
            return event
    return _keyword_extract(item, watch_profile)


def _keyword_extract(item: dict, watch_profile: dict) -> dict | None:
    rss_item = item["rss_item"]
    text = f"{rss_item.get('title', '')} {rss_item.get('summary', '')}".lower()
    event_type = _event_type(text)
    if event_type == "UNKNOWN" and not item.get("matched_terms"):
        return None
    ports = _matched_values(text, watch_profile.get("watched_ports", []))
    regions = _matched_values(text, watch_profile.get("watched_route_regions", []))
    vessel = watch_profile.get("watched_vessel")
    vessels = [vessel] if vessel and vessel.lower() in text else []
    severity = _severity(text)
    confidence = _confidence(text, ports, regions, vessels, rss_item.get("published_at"), item.get("match_score") or 0)
    source_type = _source_type(event_type)
    title = rss_item.get("title") or "External search event"
    return {
        "event_id": f"EVT-SEARCH-{abs(hash((title, rss_item.get('link')))) % 1000000:06d}",
        "source": "real_search_event_connector",
        "source_type": source_type,
        "event_type": event_type,
        "title": title,
        "description": rss_item.get("summary") or title,
        "event_time": rss_item.get("published_at"),
        "published_at": rss_item.get("published_at"),
        "locations": list(dict.fromkeys(ports + regions)),
        "affected_ports": ports,
        "affected_routes": regions,
        "affected_vessels": vessels,
        "affected_region": regions[0] if regions else (ports[0] if ports else ""),
        "severity": severity,
        "confidence": confidence,
        "url": rss_item.get("link"),
        "raw_payload": {
            "rss_item": rss_item,
            "matched_query_ids": item.get("matched_query_ids", []),
            "matched_terms": item.get("matched_terms", []),
            "match_score": item.get("match_score", 0),
            "llm_used": False,
        },
        "dedup_key": f"{source_type}|{event_type}|{title.lower()}|{rss_item.get('published_at') or ''}",
        "impact": rss_item.get("summary") or title,
        "matched_query_ids": item.get("matched_query_ids", []),
        "matched_terms": item.get("matched_terms", []),
    }


def _try_llm_extract(item: dict, watch_profile: dict) -> dict | None:
    rss_item = item["rss_item"]
    prompt = (
        "Extract one normalized shipping/trade disruption event from this news/RSS item as JSON. "
        "Allowed event_type: VESSEL_DELAY, PORT_DISRUPTION, WEATHER, SECURITY, GEOPOLITICAL, TRADE_POLICY, ROUTE_DISRUPTION, UNKNOWN. "
        "Allowed severity: LOW, MEDIUM, HIGH, CRITICAL, UNKNOWN. "
        "Do not decide relevance classification, risk level, case status, or treatment plan gating.\n"
        f"Watch profile: {json.dumps(watch_profile, ensure_ascii=True)}\n"
        f"Title: {rss_item.get('title')}\nSummary: {rss_item.get('summary')}"
    )
    payload = {
        "model": os.getenv("OPENAI_EVENT_EXTRACTION_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": "Return only JSON for a normalized event candidate."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
        parsed = json.loads(body["choices"][0]["message"]["content"])
        if not parsed.get("title"):
            return None
        fallback = _keyword_extract(item, watch_profile)
        if not fallback:
            return None
        fallback.update({key: parsed[key] for key in ["event_type", "title", "description", "locations", "affected_ports", "affected_vessels", "severity"] if key in parsed})
        fallback["confidence"] = min(1.0, float(parsed.get("confidence", fallback["confidence"])))
        fallback["raw_payload"]["llm_used"] = True
        return fallback
    except (KeyError, json.JSONDecodeError, ValueError, TimeoutError, urllib.error.URLError, urllib.error.HTTPError):
        return None


def _event_type(text: str) -> str:
    if any(term in text for term in ["strike", "labor", "shutdown", "closure", "congestion", "backlog"]):
        return "PORT_DISRUPTION"
    if any(term in text for term in ["storm", "typhoon", "cyclone", "heavy rain", "wind"]):
        return "WEATHER"
    if any(term in text for term in ["attack", "piracy", "security", "conflict"]):
        return "SECURITY"
    if any(term in text for term in ["tariff", "sanction", "customs", "import restriction"]):
        return "TRADE_POLICY"
    if any(term in text for term in ["vessel", "schedule", "eta", "delay"]):
        return "VESSEL_DELAY"
    return "UNKNOWN"


def _severity(text: str) -> str:
    if any(term in text for term in ["critical", "attack", "closure", "shutdown", "severe"]):
        return "HIGH"
    if any(term in text for term in ["delay", "congestion", "disruption", "strike"]):
        return "MEDIUM"
    return "LOW"


def _confidence(text: str, ports: list[str], regions: list[str], vessels: list[str], published_at: str | None, match_score: float) -> float:
    score = float(match_score)
    if vessels:
        score += 0.35
    if ports:
        score += 0.30
    if regions:
        score += 0.20
    if _event_type(text) != "UNKNOWN":
        score += 0.20
    if _recent(published_at):
        score += 0.10
    return min(1.0, score)


def _matched_values(text: str, values: list[str]) -> list[str]:
    return [value for value in values if value and value.lower() in text]


def _recent(value: str | None) -> bool:
    if not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed >= datetime.now(UTC) - timedelta(days=14)
    except ValueError:
        return False


def _source_type(event_type: str) -> str:
    if event_type == "WEATHER":
        return "WEATHER"
    if event_type == "TRADE_POLICY":
        return "POLICY"
    if event_type in {"SECURITY", "GEOPOLITICAL"}:
        return "GEOPOLITICAL"
    if event_type == "PORT_DISRUPTION":
        return "PORT"
    return "NEWS"
