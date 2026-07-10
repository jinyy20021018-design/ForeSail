VALID_SEQUENCE = [
    "DRAFT",
    "ACTIVE",
    "WATCHING",
    "AT_RISK",
    "ACTION_REQUIRED",
    "MONITORING",
]

ALLOWED_TRANSITIONS = {
    "DRAFT": {"ACTIVE"},
    "ACTIVE": {"WATCHING", "AT_RISK", "ACTION_REQUIRED", "MONITORING"},
    "WATCHING": {"AT_RISK", "ACTION_REQUIRED", "MONITORING"},
    "AT_RISK": {"WATCHING", "ACTION_REQUIRED", "MONITORING"},
    "ACTION_REQUIRED": {"AT_RISK", "MONITORING"},
    "MONITORING": {"WATCHING", "AT_RISK", "ACTION_REQUIRED"},
}


def can_transition(current_status: str, next_status: str) -> bool:
    return next_status in ALLOWED_TRANSITIONS.get(current_status, set())


def transition_case(case: dict, next_status: str, timeline: list[dict], reason: str) -> dict:
    current_status = case["status"]
    if current_status == next_status:
        return case
    if not can_transition(current_status, next_status):
        raise ValueError(f"Invalid status transition: {current_status} -> {next_status}")

    case["status"] = next_status
    timeline.append({"status": next_status, "reason": reason})
    return case
