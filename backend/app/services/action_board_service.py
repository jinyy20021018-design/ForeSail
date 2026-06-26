ACTION_RULES = {
    "Shipping": [
        {
            "title": "Contact carrier to confirm latest ETA and delay reason",
            "owner_role": "Logistics",
            "priority": "High",
            "deadline": "Today",
        },
        {
            "title": "Request alternative routing or discharge options",
            "owner_role": "Logistics",
            "priority": "Medium",
            "deadline": "Today",
        },
    ],
    "LC Deadline": [
        {
            "title": "Review whether delay affects latest shipment date or document presentation",
            "owner_role": "Trade Finance",
            "priority": "High",
            "deadline": "Today",
        },
        {
            "title": "Prepare LC amendment request if shipment timing becomes non-compliant",
            "owner_role": "Trade Finance",
            "priority": "High",
            "deadline": "T+1",
        },
    ],
    "Port Operation": [
        {
            "title": "Check Bangladesh / Chittagong port operation status",
            "owner_role": "Logistics",
            "priority": "High",
            "deadline": "Today",
        },
        {
            "title": "Ask freight forwarder for congestion and discharge alternatives",
            "owner_role": "Freight Forwarder",
            "priority": "Medium",
            "deadline": "Today",
        },
    ],
    "Payment Timeline": [
        {
            "title": "Update expected payment and cashflow timeline",
            "owner_role": "Finance",
            "priority": "Medium",
            "deadline": "T+1",
        },
        {
            "title": "Notify finance team of possible working capital impact",
            "owner_role": "Finance",
            "priority": "Medium",
            "deadline": "T+1",
        },
    ],
}


def generate_actions(risk_summary: dict) -> list[dict]:
    seen_titles: set[str] = set()
    actions: list[dict] = []

    exposure_categories = [exposure["category"] for exposure in risk_summary.get("exposures", [])]
    for exposure in exposure_categories:
        for rule in ACTION_RULES.get(exposure, []):
            if rule["title"] in seen_titles:
                continue
            seen_titles.add(rule["title"])
            actions.append(
                {
                    "action_id": f"ACT-{len(actions) + 1:03d}",
                    "title": rule["title"],
                    "owner_role": rule["owner_role"],
                    "priority": rule["priority"],
                    "deadline": rule["deadline"],
                    "status": "Open",
                    "related_exposure": exposure,
                }
            )

    return actions
