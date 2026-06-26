def map_event_to_exposures(event: dict, classification: str, case: dict) -> list[str]:
    if classification == "Irrelevant":
        return []

    event_type = event["type"]
    exposures: list[str] = []

    if event_type == "VESSEL_DELAY":
        exposures.extend(["Shipping", "Payment Timeline"])
        if int(event.get("delay_days") or 0) >= 3:
            exposures.append("LC Deadline")

    elif event_type in {"PORT_STRIKE", "PORT_DISRUPTION"}:
        exposures.extend(["Port Operation", "Shipping", "Payment Timeline"])

    elif event_type == "WEATHER":
        exposures.append("Shipping")
        affected_ports = set(event.get("affected_ports") or [])
        if case["port_of_loading"] in affected_ports:
            exposures.append("LC Deadline")

    elif event_type == "SECURITY":
        if event.get("affected_region") in {"East China Sea", "South China Sea", "Bay of Bengal", "Bangladesh"}:
            exposures.append("Shipping")

    elif event_type == "PORT_CONGESTION":
        affected_ports = set(event.get("affected_ports") or [])
        watched_ports = {case["port_of_loading"], case["port_of_discharge"], case["final_destination"]}
        if affected_ports.intersection(watched_ports):
            exposures.extend(["Port Operation", "Shipping"])

    return list(dict.fromkeys(exposures))


def summarize_exposures(case: dict, events: list[dict], relevance_results: list[dict]) -> dict:
    exposure_map: dict[str, dict] = {}
    trigger_events: list[str] = []
    watch_events: list[str] = []

    for result in relevance_results:
        if result["classification"] == "Relevant":
            trigger_events.append(result["event_id"])
        elif result["classification"] == "Watch":
            watch_events.append(result["event_id"])

        for exposure in result["mapped_exposures"]:
            current = exposure_map.setdefault(
                exposure,
                {
                    "category": exposure,
                    "impact": _impact_for_exposure(exposure),
                    "severity": "Medium",
                    "evidence_event_ids": [],
                    "trigger_event_ids": [],
                    "watch_event_ids": [],
                },
            )
            current["evidence_event_ids"].append(result["event_id"])

            if result["classification"] == "Relevant":
                current["trigger_event_ids"].append(result["event_id"])
                current["severity"] = "High"
            elif result["classification"] == "Watch":
                current["watch_event_ids"].append(result["event_id"])

    return {
        "triggered": bool(trigger_events),
        "trigger_events": trigger_events,
        "watch_events_considered": watch_events,
        "exposures": list(exposure_map.values()),
    }


def _impact_for_exposure(exposure: str) -> str:
    impacts = {
        "Shipping": "Shipment timing or routing may be disrupted.",
        "LC Deadline": "Delay may create latest shipment or presentation timing risk under the LC.",
        "Port Operation": "Port disruption may slow discharge or inland delivery.",
        "Payment Timeline": "ETA or discharge delay may shift expected payment and cashflow timing.",
    }
    return impacts.get(exposure, "Trade case exposure requires review.")
