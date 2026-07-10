from datetime import date, timedelta

ACTION_LEAD_DAYS = 3

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
    "Trade Compliance": [
        {
            "title": "Screen counterparties and routing against latest sanctions and tariff changes",
            "owner_role": "Trade Compliance",
            "priority": "High",
            "deadline": "Today",
        },
        {
            "title": "Verify customs and document requirements are still met under the new policy",
            "owner_role": "Trade Compliance",
            "priority": "High",
            "deadline": "T+1",
        },
    ],
}

CIF_ACTION_RULES = {
    "SELLER": [
        ("Notify buyer of shipment / delay status", "Trade Ops", "High", "Today", "SHARED"),
        ("Request updated ETA from carrier", "Logistics", "High", "Today", "SELLER"),
        ("Check LC latest shipment date", "Trade Finance", "High", "Today", "SELLER"),
        ("Check LC presentation period", "Trade Finance", "High", "Today", "SELLER"),
        ("Prepare or verify bill of lading", "Shipping Documentation", "High", "Today", "SELLER"),
        ("Prepare or verify insurance certificate", "Insurance", "High", "Today", "SELLER"),
        ("Consider LC amendment request if shipment deadline is at risk", "Trade Finance", "High", "T+1", "SELLER"),
    ],
    "BUYER": [
        ("Request updated shipment status from seller", "Procurement", "High", "Today", "SELLER"),
        ("Monitor destination port congestion", "Logistics", "High", "Today", "BUYER"),
        ("Prepare import customs documents", "Import Operations", "High", "T+1", "BUYER"),
        ("Coordinate customs broker / port agent", "Import Operations", "High", "Today", "BUYER"),
        ("Review demurrage and storage exposure", "Logistics", "High", "Today", "BUYER"),
        ("Review insurance claim procedure if cargo damage is suspected", "Insurance", "Medium", "T+1", "BUYER"),
    ],
}


def generate_actions(risk_summary: dict, facts: dict | None = None, obligations: list[dict] | None = None) -> list[dict]:
    seen_titles: set[str] = set()
    actions: list[dict] = []
    deadline_by_category = _deadline_dates_by_category(facts or {}, obligations or [])

    for exposure in risk_summary.get("exposures", []):
        category = exposure["category"]
        hazard_ids = exposure.get("hazard_ids") or []
        perspective = exposure.get("party_perspective") or risk_summary.get("trade_perspective") or "SELLER"
        incoterm_basis = exposure.get("incoterm_basis") or risk_summary.get("incoterm_basis") or ""
        if incoterm_basis == "CIF" and perspective in CIF_ACTION_RULES:
            for title, owner_role, priority, deadline, responsible_party in CIF_ACTION_RULES[perspective]:
                if not _is_relevant_cif_action(title, exposure):
                    continue
                key = f"{perspective}:{title}"
                if key in seen_titles:
                    continue
                seen_titles.add(key)
                actions.append(
                    _action(len(actions), title, owner_role, priority, deadline, category, perspective, responsible_party, "CIF", deadline_by_category, hazard_ids)
                )
            continue

        for rule in ACTION_RULES.get(category, []):
            key = f"{perspective}:{rule['title']}"
            if key in seen_titles:
                continue
            seen_titles.add(key)
            actions.append(
                _action(
                    len(actions),
                    rule["title"],
                    rule["owner_role"],
                    rule["priority"],
                    rule["deadline"],
                    category,
                    perspective,
                    "UNKNOWN",
                    incoterm_basis,
                    deadline_by_category,
                    hazard_ids,
                )
            )

    return actions


def earliest_action_deadline(actions: list[dict]) -> str | None:
    dates = sorted(action["deadline_date"] for action in actions if action.get("deadline_date"))
    return dates[0] if dates else None


def _deadline_dates_by_category(facts: dict, obligations: list[dict]) -> dict[str, str]:
    today = date.today()
    base: dict[str, str] = {}
    obligation_deadlines = {
        "Latest Shipment Date": None,
        "LC Expiry Date": None,
        "Presentation Period": None,
        "ETA / Discharge Timing": None,
    }
    for obligation in obligations:
        name = obligation.get("name")
        parsed = _parse_date(obligation.get("deadline_date"))
        if name in obligation_deadlines and parsed:
            obligation_deadlines[name] = parsed

    latest_shipment = obligation_deadlines["Latest Shipment Date"] or _parse_date(facts.get("latest_shipment_date"))
    presentation = obligation_deadlines["Presentation Period"] or _parse_date(facts.get("lc_expiry_date"))
    eta = obligation_deadlines["ETA / Discharge Timing"] or _parse_date(facts.get("eta"))

    if latest_shipment:
        base["LC Deadline"] = _clamp(latest_shipment - timedelta(days=ACTION_LEAD_DAYS), today)
        base["Shipping"] = _clamp(latest_shipment - timedelta(days=ACTION_LEAD_DAYS), today)
    if presentation:
        base["Payment Timeline"] = _clamp(presentation - timedelta(days=ACTION_LEAD_DAYS), today)
    if eta:
        base.setdefault("Port Operation", _clamp(eta - timedelta(days=ACTION_LEAD_DAYS), today))
    return base


def _action(
    index: int,
    title: str,
    owner_role: str,
    priority: str,
    deadline: str,
    exposure: str,
    perspective: str,
    responsible_party: str,
    incoterm_basis: str,
    deadline_by_category: dict[str, str] | None = None,
    hazard_ids: list[str] | None = None,
) -> dict:
    today = date.today()
    label_date = today if deadline == "Today" else today + timedelta(days=1)
    category_date = (deadline_by_category or {}).get(exposure)
    deadline_date = min(label_date.isoformat(), category_date) if category_date else label_date.isoformat()
    return {
        "action_id": f"ACT-{index + 1:03d}",
        "title": title,
        "owner_role": owner_role,
        "priority": priority,
        "deadline": deadline,
        "deadline_date": deadline_date,
        "status": "Open",
        "related_exposure": exposure,
        "party_perspective": perspective,
        "responsible_party": responsible_party,
        "incoterm_basis": incoterm_basis,
        "hazard_ids": hazard_ids or [],
    }


def _parse_date(value) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def _clamp(target: date, floor: date) -> str:
    return max(target, floor).isoformat()


def _is_relevant_cif_action(title: str, exposure: dict) -> bool:
    scenario = exposure.get("cif_scenario")
    category = exposure.get("category")
    if scenario == "destination_port_congestion":
        return title not in {"Check LC latest shipment date", "Check LC presentation period", "Consider LC amendment request if shipment deadline is at risk"}
    if scenario == "shipment_delay_before_loading":
        return title not in {"Monitor destination port congestion", "Coordinate customs broker / port agent", "Review demurrage and storage exposure"}
    if category == "LC Deadline":
        return title in {
            "Notify buyer of shipment / delay status",
            "Check LC latest shipment date",
            "Check LC presentation period",
            "Prepare or verify bill of lading",
            "Prepare or verify insurance certificate",
            "Consider LC amendment request if shipment deadline is at risk",
            "Request updated shipment status from seller",
        }
    return True
