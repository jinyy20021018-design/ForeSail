from app.services.port_registry_service import resolve_port
from app.services.route_region_service import event_text_mentions_corridor, merge_watched_route_regions

LEG_ORDER = ["PRE_CARRIAGE", "PORT_OF_LOADING", "MAIN_CARRIAGE", "DESTINATION"]

INCOTERM_RULES: dict[str, dict] = {
    "EXW": {
        "risk_transfer_leg": "PRE_CARRIAGE",
        "risk_transfer_point": "At seller's premises when goods are made available",
        "main_carriage_by": "BUYER",
        "insurance_obligation": None,
    },
    "FCA": {
        "risk_transfer_leg": "PRE_CARRIAGE",
        "risk_transfer_point": "On handover to the buyer-nominated carrier at the named place",
        "main_carriage_by": "BUYER",
        "insurance_obligation": None,
    },
    "FAS": {
        "risk_transfer_leg": "PORT_OF_LOADING",
        "risk_transfer_point": "Alongside the vessel at the port of loading",
        "main_carriage_by": "BUYER",
        "insurance_obligation": None,
    },
    "FOB": {
        "risk_transfer_leg": "PORT_OF_LOADING",
        "risk_transfer_point": "On board the vessel at the port of loading",
        "main_carriage_by": "BUYER",
        "insurance_obligation": None,
    },
    "CFR": {
        "risk_transfer_leg": "PORT_OF_LOADING",
        "risk_transfer_point": "On board the vessel at the port of loading",
        "main_carriage_by": "SELLER",
        "insurance_obligation": None,
    },
    "CIF": {
        "risk_transfer_leg": "PORT_OF_LOADING",
        "risk_transfer_point": "On board vessel at port of loading",
        "main_carriage_by": "SELLER",
        "insurance_obligation": "Seller provides minimum ICC(C) cargo cover to the named destination port",
    },
    "CPT": {
        "risk_transfer_leg": "PRE_CARRIAGE",
        "risk_transfer_point": "On handover to the first carrier",
        "main_carriage_by": "SELLER",
        "insurance_obligation": None,
    },
    "CIP": {
        "risk_transfer_leg": "PRE_CARRIAGE",
        "risk_transfer_point": "On handover to the first carrier",
        "main_carriage_by": "SELLER",
        "insurance_obligation": "Seller provides ICC(A) all-risk cargo cover to the named place",
    },
    "DAP": {
        "risk_transfer_leg": "DESTINATION",
        "risk_transfer_point": "At the named destination, ready for unloading",
        "main_carriage_by": "SELLER",
        "insurance_obligation": None,
    },
    "DPU": {
        "risk_transfer_leg": "DESTINATION",
        "risk_transfer_point": "At the named destination, once unloaded",
        "main_carriage_by": "SELLER",
        "insurance_obligation": None,
    },
    "DDP": {
        "risk_transfer_leg": "DESTINATION",
        "risk_transfer_point": "At the named destination, cleared for import",
        "main_carriage_by": "SELLER",
        "insurance_obligation": None,
    },
}


def resolve_cif_responsibility(case: dict) -> dict:
    incoterm = str(case.get("incoterm") or "").strip().upper()
    named_place = (
        case.get("incoterm_named_place")
        or case.get("port_of_discharge")
        or case.get("final_destination")
        or ""
    )
    is_cif = incoterm.startswith("CIF")
    warnings: list[str] = []
    if not is_cif:
        warnings.append("INCOTERM_NOT_CIF")
    if is_cif and not named_place:
        warnings.append("CIF_NAMED_DESTINATION_PORT_MISSING")

    return {
        "incoterm": "CIF" if is_cif else (incoterm or "UNKNOWN"),
        "named_destination_port": named_place,
        "risk_transfer_point": "On board vessel at port of loading" if is_cif else "Not determined",
        "cost_responsibility_until": named_place if is_cif else "Not determined",
        "seller_responsibilities": [
            "Arrange carriage to named destination port",
            "Procure minimum cargo insurance cover",
            "Provide commercial invoice and transport documents",
            "Load goods on board at port of loading",
        ] if is_cif else [],
        "buyer_responsibilities": [
            "Bear cargo risk after goods are on board",
            "Handle import clearance unless otherwise agreed",
            "Take delivery at destination",
            "Manage downstream disruption after destination arrival",
        ] if is_cif else [],
        "warnings": warnings,
    }


def attribute_event(case: dict, event: dict) -> dict:
    incoterm = str(case.get("incoterm") or "").strip().upper()[:3]
    rules = INCOTERM_RULES.get(incoterm)
    perspective = str(case.get("trade_perspective") or "SELLER").strip().upper()
    if perspective not in {"SELLER", "BUYER"}:
        perspective = "SELLER"
    legs_hit = legs_hit_by_event(case, event)
    payment_method = str(case.get("payment_method") or "").upper()
    lc_based = "LC" in payment_method or "LETTER OF CREDIT" in payment_method

    if rules is None:
        return {
            "incoterm": incoterm or "UNKNOWN",
            "trade_perspective": perspective,
            "legs_hit": legs_hit,
            "risk_transfer_point": "Not determined",
            "cargo_risk_owner_by_leg": {},
            "our_cargo_risk": True,
            "our_payment_risk": lc_based and perspective == "SELLER" and _hits_pre_transfer(legs_hit),
            "controls_main_carriage": None,
            "insurance_note": "Incoterm unknown; insurance obligations not determined.",
            "monitor_worthy": True,
            "attribution_note": "Incoterm is unknown, so the event is conservatively treated as our exposure.",
            "warnings": ["INCOTERM_UNKNOWN"],
        }

    transfer_index = LEG_ORDER.index(rules["risk_transfer_leg"])
    owners = {leg: ("SELLER" if LEG_ORDER.index(leg) <= transfer_index else "BUYER") for leg in legs_hit}
    our_cargo_risk = any(owner == perspective for owner in owners.values())
    counterparty_cargo_risk = any(owner != perspective for owner in owners.values())
    our_payment_risk = perspective == "SELLER" and lc_based and _hits_pre_transfer(legs_hit)
    controls_main_carriage = rules["main_carriage_by"] == perspective
    residual_duty = perspective == "SELLER" and rules["main_carriage_by"] == "SELLER" and counterparty_cargo_risk
    monitor_worthy = bool(legs_hit) and (
        our_cargo_risk
        or our_payment_risk
        or residual_duty
        or (controls_main_carriage and "MAIN_CARRIAGE" in legs_hit)
    )

    warnings: list[str] = []
    if incoterm == "CIF" and perspective == "BUYER" and any(leg in {"MAIN_CARRIAGE", "DESTINATION"} for leg in legs_hit):
        warnings.append("CIF_MIN_COVER_GAP")

    return {
        "incoterm": incoterm,
        "trade_perspective": perspective,
        "legs_hit": legs_hit,
        "risk_transfer_point": rules["risk_transfer_point"],
        "cargo_risk_owner_by_leg": owners,
        "our_cargo_risk": our_cargo_risk,
        "our_payment_risk": our_payment_risk,
        "controls_main_carriage": controls_main_carriage,
        "insurance_note": rules["insurance_obligation"]
        or f"No mandatory cargo insurance under {incoterm}; each party covers its own risk portion.",
        "monitor_worthy": monitor_worthy,
        "attribution_note": _attribution_note(incoterm, perspective, legs_hit, owners, our_payment_risk, rules),
        "warnings": warnings,
    }


def legs_hit_by_event(case: dict, event: dict) -> list[str]:
    legs: list[str] = []
    affected_ports = {str(port).strip().lower() for port in (event.get("affected_ports") or []) if str(port).strip()}

    def _port_matches(port_name) -> bool:
        if not port_name or str(port_name).strip().upper() == "TBD":
            return False
        target = str(port_name).strip().lower()
        return any(target == port or target in port or port in target for port in affected_ports)

    if _port_matches(case.get("port_of_loading")):
        legs.append("PORT_OF_LOADING")
    if _port_matches(case.get("port_of_discharge")) or _port_matches(case.get("final_destination")):
        legs.append("DESTINATION")

    region = str(event.get("affected_region") or "").strip()
    if region:
        if "PORT_OF_LOADING" not in legs and _region_of(case.get("port_of_loading")) == region:
            legs.append("PORT_OF_LOADING")
        if "DESTINATION" not in legs and region in {
            _region_of(case.get("port_of_discharge")),
            _region_of(case.get("final_destination")),
        }:
            legs.append("DESTINATION")

    if not legs:
        vessel = case.get("vessel")
        vessel_match = bool(vessel) and (
            event.get("affected_vessel") == vessel or vessel in (event.get("affected_vessels") or [])
        )
        corridors = set(merge_watched_route_regions(case))
        if vessel_match or region in corridors or event_text_mentions_corridor(event, corridors):
            legs.append("MAIN_CARRIAGE")

    return legs


def _region_of(port_name) -> str | None:
    record = resolve_port(port_name)
    return record["region"] if record else None


def _hits_pre_transfer(legs_hit: list[str]) -> bool:
    return any(leg in {"PRE_CARRIAGE", "PORT_OF_LOADING"} for leg in legs_hit)


def _attribution_note(incoterm: str, perspective: str, legs_hit: list[str], owners: dict, our_payment_risk: bool, rules: dict) -> str:
    if not legs_hit:
        return "Event does not map to any leg of this shipment's route."
    leg_text = ", ".join(f"{leg.replace('_', ' ').lower()} (cargo risk: {owners[leg]})" for leg in legs_hit)
    parts = [f"Under {incoterm}, event hits {leg_text}; risk transfers {rules['risk_transfer_point'].lower()}."]
    if our_payment_risk:
        parts.append(
            f"As {perspective} paid under LC, a disruption before loading threatens the latest shipment date and therefore payment."
        )
    controller = rules["main_carriage_by"]
    parts.append(f"{controller} arranges the main carriage and holds rerouting decisions.")
    return " ".join(parts)
