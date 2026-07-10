def generate_action_drafts(case_id: str, facts: dict, risk_summary: dict, actions: list[dict], hazards: list[dict] | None = None) -> list[dict]:
    exposures = {exposure["category"] for exposure in risk_summary.get("exposures", [])}
    hazards = hazards or []
    vessel = facts.get("vessel") or "the nominated vessel"
    route = facts.get("route") or "the contracted route"
    pol = facts.get("port_of_loading") or "the port of loading"
    pod = facts.get("port_of_discharge") or "the port of discharge"
    final_destination = facts.get("final_destination") or pod
    incoterm = str(facts.get("incoterm") or "").upper()
    perspective = str(facts.get("trade_perspective") or "SELLER").upper()
    drafts: list[dict] = []

    if "Shipping" in exposures:
        drafts.append(_draft(
            case_id,
            "CARRIER_ETA_INQUIRY",
            "Carrier ETA Inquiry Draft",
            "Carrier / Freight Forwarder",
            (
                f"Please confirm the latest ETA and delay reason for vessel {vessel} "
                f"on route {route}. Current case ETA is {facts.get('eta')}. "
                f"Please also confirm whether the delay affects discharge at {pod} and onward delivery to {final_destination}."
                f"{_trigger_sentence(hazards, 'Shipping')}"
            ),
            actions,
            "Shipping",
            hazards,
        ))

    if "LC Deadline" in exposures:
        drafts.append(_draft(
            case_id,
            "LC_AMENDMENT_INTERNAL_REQUEST",
            "LC Amendment Internal Request",
            "Trade Finance",
            (
                f"Please review whether LC amendment is needed. Latest shipment date is {facts.get('latest_shipment_date')}; "
                f"current vessel/route timing indicates delay risk for {vessel}. "
                f"As {perspective} under {incoterm or 'the agreed incoterm'}, missing the latest shipment date risks documentary non-compliance. "
                "This is a preliminary operational assessment and not a bank document examination conclusion."
                f"{_trigger_sentence(hazards, 'LC Deadline')}"
            ),
            actions,
            "LC Deadline",
            hazards,
        ))

    if "Payment Timeline" in exposures or "LC Deadline" in exposures:
        drafts.append(_draft(
            case_id,
            "TRADE_FINANCE_ALERT",
            "Trade Finance Alert Draft",
            "Finance / Trade Finance",
            (
                f"Potential payment timeline impact detected for {facts.get('payment_method')} shipment. "
                f"ETA is {facts.get('eta')}; amount is {facts.get('currency')} {facts.get('amount')}. "
                "Please review working capital and presentation timing assumptions."
                f"{_trigger_sentence(hazards, 'Payment Timeline')}"
            ),
            actions,
            "Payment Timeline",
            hazards,
        ))

    if "Port Operation" in exposures:
        drafts.append(_draft(
            case_id,
            "PORT_STATUS_INQUIRY",
            "Port Status Inquiry Draft",
            "Freight Forwarder / Local Agent",
            (
                f"Please provide the latest port operation status for {pod}"
                f"{f' and {final_destination}' if final_destination != pod else ''}, including strike impact, "
                "berthing delays, discharge constraints, and inland delivery availability."
                f"{_trigger_sentence(hazards, 'Port Operation')}"
            ),
            actions,
            "Port Operation",
            hazards,
        ))

    if "Trade Compliance" in exposures:
        drafts.append(_draft(
            case_id,
            "TRADE_COMPLIANCE_REVIEW",
            "Trade Compliance Review Draft",
            "Trade Compliance",
            (
                f"A sanctions, tariff, or customs policy change may affect this shipment ({pol} to {final_destination}, "
                f"{incoterm or 'incoterm TBD'}). Please screen counterparties, routing, and document requirements "
                "against the latest policy update and confirm clearance is still possible as planned."
                f"{_trigger_sentence(hazards, 'Trade Compliance')}"
            ),
            actions,
            "Trade Compliance",
            hazards,
        ))

    for index, draft in enumerate(drafts, start=1):
        draft["draft_id"] = f"DRAFT-{index:03d}"
    return drafts


def _trigger_sentence(hazards: list[dict], category: str) -> str:
    matched = [hazard for hazard in hazards if category in (hazard.get("mapped_exposures") or [])]
    if not matched:
        return ""
    parts = []
    for hazard in matched[:2]:
        window = hazard.get("expected_impact_window") or {}
        window_text = f" (expected impact {str(window.get('start'))[:10]} to {str(window.get('end'))[:10]})" if window.get("start") else ""
        parts.append(f"{hazard.get('title')}{window_text}")
    return f" Trigger: {'; '.join(parts)}."


def _draft(case_id: str, draft_type: str, title: str, recipient_role: str, body: str, actions: list[dict], category: str, hazards: list[dict]) -> dict:
    related = [action["action_id"] for action in actions if action.get("related_exposure") == category]
    hazard_ids = [hazard["hazard_id"] for hazard in hazards if category in (hazard.get("mapped_exposures") or [])]
    return {
        "draft_id": "",
        "case_id": case_id,
        "draft_type": draft_type,
        "title": title,
        "recipient_role": recipient_role,
        "body": body,
        "related_actions": related or [action["action_id"] for action in actions],
        "hazard_ids": hazard_ids,
        "status": "DRAFT",
        "requires_user_review": True,
    }
