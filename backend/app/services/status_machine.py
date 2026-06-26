VALID_SEQUENCE = [
    "DRAFT",
    "ACTIVE",
    "WATCHING",
    "AT_RISK",
    "ACTION_REQUIRED",
    "MONITORING",
]


def can_transition(current_status: str, next_status: str) -> bool:
    try:
        return VALID_SEQUENCE.index(next_status) >= VALID_SEQUENCE.index(current_status)
    except ValueError:
        return False


def transition_case(case: dict, next_status: str, timeline: list[dict], reason: str) -> dict:
    current_status = case["status"]
    if current_status == next_status:
        return case
    if not can_transition(current_status, next_status):
        raise ValueError(f"Invalid status transition: {current_status} -> {next_status}")

    case["status"] = next_status
    timeline.append({"status": next_status, "reason": reason})
    return case
