from app.services.document_service import add_days, get_extracted_fields


def generate_obligations(case_id: str, facts: dict, relevance_results: list[dict], risk_summary: dict) -> list[dict]:
    fields = get_extracted_fields(case_id)
    field_by_name = {field["field_name"]: field for field in fields}
    event_types = {result["event_id"]: result for result in relevance_results}
    exposure_categories = {exposure["category"] for exposure in risk_summary.get("exposures", [])}
    has_vessel_delay = "EVT-001" in event_types and event_types["EVT-001"]["classification"] == "Relevant"
    has_port_strike = "EVT-002" in event_types and event_types["EVT-002"]["classification"] == "Relevant"

    return [
        {
            "obligation_id": "OBL-001",
            "case_id": case_id,
            "name": "Latest Shipment Date",
            "source": "LC",
            "source_document_id": _doc_id(field_by_name, "latest_shipment_date"),
            "deadline_date": facts.get("latest_shipment_date", ""),
            "current_assessment": "At risk due to vessel delay" if has_vessel_delay or "Shipping" in exposure_categories else "No immediate breach",
            "severity": "High" if has_vessel_delay or "Shipping" in exposure_categories else "Medium",
            "recommended_action": "Prepare LC amendment review",
            "evidence_field_ids": _field_ids(field_by_name, ["latest_shipment_date"]),
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
            "current_assessment": "No immediate breach",
            "severity": "Medium",
            "recommended_action": "Continue monitoring",
            "evidence_field_ids": _field_ids(field_by_name, ["lc_expiry_date"]),
            "status": "OPEN",
            "assessment_notice": "Preliminary operational assessment only. Not legal, banking, or insurance advice.",
        },
        {
            "obligation_id": "OBL-003",
            "case_id": case_id,
            "name": "Presentation Period",
            "source": "LC",
            "source_document_id": _doc_id(field_by_name, "presentation_period_days"),
            "deadline_date": add_days(facts.get("latest_shipment_date", ""), facts.get("presentation_period_days")),
            "current_assessment": "May be compressed" if "Shipping" in exposure_categories else "No immediate breach",
            "severity": "High" if "Shipping" in exposure_categories else "Medium",
            "recommended_action": "Alert Trade Finance",
            "evidence_field_ids": _field_ids(field_by_name, ["presentation_period_days", "latest_shipment_date"]),
            "status": "OPEN",
            "assessment_notice": "Preliminary operational assessment only. Not legal, banking, or insurance advice.",
        },
        {
            "obligation_id": "OBL-004",
            "case_id": case_id,
            "name": "ETA / Discharge Timing",
            "source": "Booking",
            "source_document_id": _doc_id(field_by_name, "eta"),
            "deadline_date": facts.get("eta", ""),
            "current_assessment": "Delayed / at risk" if has_vessel_delay or has_port_strike else "No immediate breach",
            "severity": "High" if has_vessel_delay or has_port_strike else "Medium",
            "recommended_action": "Confirm updated ETA with carrier",
            "evidence_field_ids": _field_ids(field_by_name, ["eta"]),
            "status": "OPEN",
            "assessment_notice": "Preliminary operational assessment only. Not legal, banking, or insurance advice.",
        },
    ]


def _field_ids(field_by_name: dict, names: list[str]) -> list[str]:
    return [field_by_name[name]["field_id"] for name in names if name in field_by_name]


def _doc_id(field_by_name: dict, name: str) -> str | None:
    return field_by_name[name]["source_document_id"] if name in field_by_name else None
