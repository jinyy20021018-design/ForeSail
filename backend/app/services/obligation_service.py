from datetime import date

from app.services.document_service import add_days, get_extracted_fields

DISRUPTION_EVENT_TYPES = {
    "WEATHER",
    "PORT_STRIKE",
    "PORT_DISRUPTION",
    "PORT_CONGESTION",
    "VESSEL_DELAY",
    "SECURITY",
    "GEOPOLITICAL",
    "ROUTE_DISRUPTION",
}


def generate_obligations(case_id: str, facts: dict, relevance_results: list[dict], risk_summary: dict) -> list[dict]:
    fields = get_extracted_fields(case_id)
    field_by_name = {field["field_name"]: field for field in fields}
    exposure_categories = {exposure["category"] for exposure in risk_summary.get("exposures", [])}

    relevant = [result for result in relevance_results if result["classification"] == "Relevant"]
    watch = [result for result in relevance_results if result["classification"] == "Watch"]
    pol_threats_relevant = [result for result in relevant if _threatens_loading(result)]
    pol_threats_watch = [result for result in watch if _threatens_loading(result)]
    destination_threats = [result for result in relevant if _hits_leg(result, "DESTINATION")]
    max_arrival_delay = max(
        (int(result.get("delay_days") or 0) for result in relevant if _event_type(result) == "VESSEL_DELAY"),
        default=0,
    )

    pol = facts.get("port_of_loading") or "port of loading"
    etd = facts.get("etd", "")
    eta = facts.get("eta", "")
    latest_shipment = facts.get("latest_shipment_date", "")
    buffer_days = _days_between(etd, latest_shipment)

    if pol_threats_relevant:
        buffer_text = f" Only {buffer_days} day(s) of buffer between planned ETD {etd} and the latest shipment date." if buffer_days is not None else ""
        latest_shipment_assessment = (
            f"At risk: {_titles(pol_threats_relevant)} may disrupt departure at {pol} before loading.{buffer_text}"
        )
        latest_shipment_severity = "High"
    elif pol_threats_watch:
        latest_shipment_assessment = (
            f"Watch: possible departure disruption at {pol} ({_titles(pol_threats_watch)}); monitor loading schedule against the latest shipment date."
        )
        latest_shipment_severity = "Medium"
    elif "Shipping" in exposure_categories:
        latest_shipment_assessment = "Shipping exposure present; verify the loading schedule still meets the latest shipment date."
        latest_shipment_severity = "Medium"
    else:
        latest_shipment_assessment = "No immediate breach"
        latest_shipment_severity = "Medium"

    if max_arrival_delay > 0:
        projected_eta = add_days(eta, max_arrival_delay) if eta else ""
        eta_assessment = f"Delayed: projected ETA slips from {eta} to {projected_eta} (+{max_arrival_delay} days)."
        eta_severity = "High"
    elif destination_threats:
        eta_assessment = f"At risk: {_titles(destination_threats)} may slow discharge or inland delivery."
        eta_severity = "High"
    else:
        eta_assessment = "No immediate breach"
        eta_severity = "Medium"

    presentation_at_risk = bool(pol_threats_relevant) or "Shipping" in exposure_categories
    lc_amendment_needed = bool(pol_threats_relevant) or "LC Deadline" in exposure_categories

    pol_hazard_ids = _hazard_ids(pol_threats_relevant + pol_threats_watch)
    eta_hazard_ids = _hazard_ids(destination_threats + [result for result in relevant if _event_type(result) == "VESSEL_DELAY"])

    return [
        {
            "obligation_id": "OBL-001",
            "case_id": case_id,
            "name": "Latest Shipment Date",
            "source": "LC",
            "source_document_id": _doc_id(field_by_name, "latest_shipment_date"),
            "deadline_date": latest_shipment,
            "current_assessment": latest_shipment_assessment,
            "severity": latest_shipment_severity,
            "recommended_action": "Prepare LC amendment review" if latest_shipment_severity == "High" else "Continue monitoring",
            "evidence_field_ids": _field_ids(field_by_name, ["latest_shipment_date"]),
            "hazard_ids": pol_hazard_ids,
            "status": "OPEN",
            "assessment_notice": "Preliminary operational assessment only. Not legal, banking, or insurance advice.",
        },
        {
            "obligation_id": "OBL-002",
            "case_id": case_id,
            "name": "LC Expiry Date",
            "source": "LC",
            "source_document_id": _doc_id(field_by_name, "lc_expiry_date"),
            "deadline_date": facts.get("lc_expiry_date", ""),
            "current_assessment": "Amendment may be required if the shipment date moves." if lc_amendment_needed else "No immediate breach",
            "severity": "High" if lc_amendment_needed else "Medium",
            "recommended_action": "Review LC amendment need with Trade Finance" if lc_amendment_needed else "Continue monitoring",
            "evidence_field_ids": _field_ids(field_by_name, ["lc_expiry_date"]),
            "hazard_ids": pol_hazard_ids,
            "status": "OPEN",
            "assessment_notice": "Preliminary operational assessment only. Not legal, banking, or insurance advice.",
        },
        {
            "obligation_id": "OBL-003",
            "case_id": case_id,
            "name": "Presentation Period",
            "source": "LC",
            "source_document_id": _doc_id(field_by_name, "presentation_period_days"),
            "deadline_date": add_days(latest_shipment, facts.get("presentation_period_days")),
            "current_assessment": "May be compressed if the shipment date slips toward the latest shipment date." if presentation_at_risk else "No immediate breach",
            "severity": "High" if presentation_at_risk else "Medium",
            "recommended_action": "Alert Trade Finance" if presentation_at_risk else "Continue monitoring",
            "evidence_field_ids": _field_ids(field_by_name, ["presentation_period_days", "latest_shipment_date"]),
            "hazard_ids": pol_hazard_ids,
            "status": "OPEN",
            "assessment_notice": "Preliminary operational assessment only. Not legal, banking, or insurance advice.",
        },
        {
            "obligation_id": "OBL-004",
            "case_id": case_id,
            "name": "ETA / Discharge Timing",
            "source": "Booking",
            "source_document_id": _doc_id(field_by_name, "eta"),
            "deadline_date": eta,
            "current_assessment": eta_assessment,
            "severity": eta_severity,
            "recommended_action": "Confirm updated ETA with carrier" if eta_severity == "High" else "Continue monitoring",
            "evidence_field_ids": _field_ids(field_by_name, ["eta"]),
            "hazard_ids": eta_hazard_ids,
            "status": "OPEN",
            "assessment_notice": "Preliminary operational assessment only. Not legal, banking, or insurance advice.",
        },
    ]


def _event_type(result: dict) -> str:
    return str(result.get("event_type") or "").upper()


def _hits_leg(result: dict, leg: str) -> bool:
    return leg in (result.get("attribution") or {}).get("legs_hit", [])


def _threatens_loading(result: dict) -> bool:
    if _event_type(result) not in DISRUPTION_EVENT_TYPES:
        return False
    return _hits_leg(result, "PORT_OF_LOADING") or _hits_leg(result, "PRE_CARRIAGE")


def _titles(results: list[dict]) -> str:
    return "; ".join(str(result.get("title") or result.get("event_id") or "external event") for result in results[:3])


def _hazard_ids(results: list[dict]) -> list[str]:
    return list(dict.fromkeys(result["hazard_id"] for result in results if result.get("hazard_id")))


def _days_between(start: str, end: str) -> int | None:
    try:
        return (date.fromisoformat(str(end)[:10]) - date.fromisoformat(str(start)[:10])).days
    except (ValueError, TypeError):
        return None


def _field_ids(field_by_name: dict, names: list[str]) -> list[str]:
    return [field_by_name[name]["field_id"] for name in names if name in field_by_name]


def _doc_id(field_by_name: dict, name: str) -> str | None:
    return field_by_name[name]["source_document_id"] if name in field_by_name else None

