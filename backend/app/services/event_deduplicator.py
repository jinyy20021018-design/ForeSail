SOURCE_RANK = {
    "WEATHER": 5,
    "PORT": 5,
    "NEWS": 4,
    "GEOPOLITICAL": 4,
    "POLICY": 4,
    "MANUAL": 3,
    "MOCK": 2,
}


def deduplicate_events(events: list[dict]) -> tuple[list[dict], dict]:
    by_key: dict[str, dict] = {}
    duplicates_removed = 0
    for event in events:
        key = event.get("dedup_key") or _fallback_key(event)
        current = by_key.get(key)
        if current is None:
            by_key[key] = event
            continue
        duplicates_removed += 1
        if _rank(event) > _rank(current):
            by_key[key] = event
    deduped = list(by_key.values())
    return deduped, {
        "input_count": len(events),
        "deduped_count": len(deduped),
        "duplicates_removed": duplicates_removed,
    }


def _fallback_key(event: dict) -> str:
    return "|".join([
        str(event.get("source_type") or ""),
        str(event.get("title") or "").lower(),
        str(event.get("event_time") or ""),
    ])


def _rank(event: dict) -> tuple[int, float]:
    return (SOURCE_RANK.get(str(event.get("source_type") or "UNKNOWN"), 0), float(event.get("confidence") or 0))
