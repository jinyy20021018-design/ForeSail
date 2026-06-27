from app.services.case_service import (
    get_actions,
    get_case,
    get_relevance_results,
    get_risk_summary,
    set_trade_perspective,
)
from app.services.document_service import get_information_gaps, get_obligations
from app.services.incoterm_rule_service import resolve_cif_responsibility
from app.services.persistence_service import list_items

SUPPORTED_PERSPECTIVES = {"BUYER", "SELLER"}
DEFAULT_PERSPECTIVE = "SELLER"
UNSUPPORTED_PERSPECTIVE_ERROR = {
    "error": "UNSUPPORTED_PERSPECTIVE",
    "message": "Only BUYER and SELLER perspectives are supported in this MVP.",
}


class UnsupportedPerspectiveError(ValueError):
    pass


def normalize_perspective(value: str | None) -> str:
    perspective = str(value or DEFAULT_PERSPECTIVE).strip().upper()
    if perspective not in SUPPORTED_PERSPECTIVES:
        raise UnsupportedPerspectiveError(perspective)
    return perspective


def update_case_perspective(case_id: str, perspective: str) -> dict:
    return set_trade_perspective(case_id, normalize_perspective(perspective))


def perspective_analysis(case_id: str, perspective: str | None = None) -> dict:
    case = get_case(case_id)
    selected = normalize_perspective(perspective or case.get("trade_perspective"))
    responsibility = resolve_cif_responsibility(case)
    return {
        "case_id": case_id,
        "trade_perspective": selected,
        "cif_responsibility": responsibility,
        "risk_summary": _filter_for_perspective(get_risk_summary(case_id), selected),
        "obligations": _filter_list(get_obligations(case_id), selected),
        "information_gaps": _filter_list(get_information_gaps(case_id), selected),
        "actions": _filter_list(get_actions(case_id), selected),
        "treatment_plans": [_shape_plan_for_perspective(plan, selected) for plan in _list_treatment_plan_items(case_id)],
        "relevance_results": get_relevance_results(case_id),
    }


def _filter_for_perspective(risk_summary: dict, perspective: str) -> dict:
    output = dict(risk_summary or {})
    output["exposures"] = _filter_list(output.get("exposures", []), perspective)
    output["trade_perspective"] = perspective
    output["incoterm_basis"] = "CIF"
    return output


def _filter_list(items: list[dict], perspective: str) -> list[dict]:
    filtered = []
    for item in items:
        item_perspective = item.get("party_perspective") or item.get("perspective")
        if item_perspective in {None, "", perspective}:
            filtered.append(item)
    return filtered


def _list_treatment_plan_items(case_id: str) -> list[dict]:
    plans = [plan for plan in list_items("treatment_plan", case_id) if isinstance(plan, dict)]
    return sorted(plans, key=lambda plan: plan.get("plan_id", ""))


def _shape_plan_for_perspective(plan: dict, perspective: str) -> dict:
    output = dict(plan)
    output["perspective"] = perspective
    output["incoterm_basis"] = output.get("incoterm_basis") or "CIF"
    if perspective == plan.get("perspective"):
        return output
    if perspective == "BUYER":
        output["summary"] = "Buyer perspective: manage arrival delay, import clearance readiness, port congestion, demurrage/storage exposure, inland delivery planning, and insurance claim route if cargo risk materializes."
        output["covered_risks"] = ["Arrival delay risk", "Import clearance readiness", "Port congestion handling", "Demurrage/storage exposure"]
        output["required_actions"] = [
            "Request updated shipment status from seller",
            "Monitor destination port congestion",
            "Prepare import customs documents",
            "Coordinate customs broker / port agent",
            "Review demurrage and storage exposure",
            "Review insurance claim procedure if cargo damage is suspected",
        ]
        output["rationale"] = "Buyer perspective under CIF focuses on risk after loading and destination-side operational exposure."
    else:
        output["summary"] = "Seller perspective: protect LC deadlines, shipment compliance, document presentation, carrier ETA inquiry, buyer notification, insurance certificate readiness, and possible LC amendment."
        output["covered_risks"] = ["LC deadline protection", "Shipment compliance", "Document presentation", "Carrier ETA uncertainty"]
        output["required_actions"] = [
            "Notify buyer of shipment / delay status",
            "Request updated ETA from carrier",
            "Check LC latest shipment date",
            "Check LC presentation period",
            "Prepare or verify bill of lading",
            "Prepare or verify insurance certificate",
            "Consider LC amendment request if shipment deadline is at risk",
        ]
        output["rationale"] = "Seller perspective under CIF focuses on freight, insurance, document, shipment, and LC compliance obligations."
    output["residual_risks"] = [_shape_residual_for_perspective(risk, perspective) for risk in output.get("residual_risks", [])]
    return output


def _shape_residual_for_perspective(risk: dict, perspective: str) -> dict:
    output = dict(risk)
    output["perspective"] = perspective
    output["incoterm_basis"] = output.get("incoterm_basis") or "CIF"
    if perspective == "BUYER" and "Buyer" not in output.get("risk_title", ""):
        output["risk_title"] = "Buyer destination-side exposure remains uncertain"
        output["description"] = "Arrival, import clearance, port delay, demurrage/storage, and cargo condition facts may change after the current assessment."
        output["owner_role"] = "Import Operations"
    elif perspective == "SELLER" and "Buyer" not in output.get("risk_title", ""):
        output["risk_title"] = "Seller LC and shipment compliance exposure remains uncertain"
        output["description"] = "Shipment timing, document presentation, carrier ETA, and insurance certificate readiness may still need confirmation."
        output["owner_role"] = "Trade Finance"
    return output
