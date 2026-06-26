def generate_action_drafts(case_id: str, facts: dict, risk_summary: dict, actions: list[dict]) -> list[dict]:
    exposures = {exposure["category"] for exposure in risk_summary.get("exposures", [])}
    drafts: list[dict] = []

    if "Shipping" in exposures:
        drafts.append(_draft(
            case_id,
            "CARRIER_ETA_INQUIRY",
            "Carrier ETA Inquiry Draft",
            "Carrier / Freight Forwarder",
            (
                f"Please confirm the latest ETA and delay reason for vessel {facts.get('vessel')} "
                f"on route {facts.get('route')}. Current case ETA is {facts.get('eta')}. "
                "Please also confirm whether the delay affects discharge at Chittagong and onward delivery to Dhaka."
            ),
            actions,
        ))

    if "LC Deadline" in exposures:
        drafts.append(_draft(
            case_id,
            "LC_AMENDMENT_INTERNAL_REQUEST",
            "LC Amendment Internal Request",
            "Trade Finance",
            (
                f"Please review whether LC amendment is needed. Latest shipment date is {facts.get('latest_shipment_date')}; "
                f"current vessel/route timing indicates delay risk for {facts.get('vessel')}. "
                "This is a preliminary operational assessment and not a bank document examination conclusion."
            ),
            actions,
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
            ),
            actions,
        ))

    if "Port Operation" in exposures:
        drafts.append(_draft(
            case_id,
            "PORT_STATUS_INQUIRY",
            "Port Status Inquiry Draft",
            "Freight Forwarder / Local Agent",
            (
                "Please provide latest Bangladesh / Chittagong port operation status, including strike impact, "
                "berthing delays, discharge constraints, and inland delivery availability."
            ),
            actions,
        ))

    for index, draft in enumerate(drafts, start=1):
        draft["draft_id"] = f"DRAFT-{index:03d}"
    return drafts


def _draft(case_id: str, draft_type: str, title: str, recipient_role: str, body: str, actions: list[dict]) -> dict:
    return {
        "draft_id": "",
        "case_id": case_id,
        "draft_type": draft_type,
        "title": title,
        "recipient_role": recipient_role,
        "body": body,
        "related_actions": [action["action_id"] for action in actions],
        "status": "DRAFT",
        "requires_user_review": True,
    }
