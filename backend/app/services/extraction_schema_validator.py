from datetime import datetime

ALLOWED_FIELDS = {
    "buyer",
    "seller",
    "commodity",
    "quantity",
    "amount",
    "currency",
    "incoterm",
    "payment_method",
    "vessel",
    "route",
    "port_of_loading",
    "port_of_discharge",
    "final_destination",
    "etd",
    "eta",
    "latest_shipment_date",
    "lc_expiry_date",
    "presentation_period_days",
    "booking_reference",
    "lc_number",
    "issuing_bank",
    "beneficiary",
    "applicant",
    "insurance_policy_number",
    "coverage_type",
    "case_name",
}

DATE_FIELDS = {"etd", "eta", "latest_shipment_date", "lc_expiry_date"}


def validate_extracted_fields(items: list[dict] | None, document: dict) -> tuple[list[dict], list[str]]:
    warnings: list[str] = []
    valid: list[dict] = []
    if not isinstance(items, list):
        return [], ["LLM output did not contain a fields array."]

    for item in items:
        if not isinstance(item, dict):
            warnings.append("Skipped non-object field item.")
            continue
        field_name = str(item.get("field_name") or "").strip()
        value = item.get("value")
        if field_name not in ALLOWED_FIELDS:
            warnings.append(f"Skipped unsupported field: {field_name or 'UNKNOWN'}.")
            continue
        if value in {None, ""}:
            warnings.append(f"Skipped empty field: {field_name}.")
            continue

        confidence = _confidence(item.get("confidence"))
        evidence = str(item.get("evidence_text") or item.get("evidence") or "").strip()
        if not evidence:
            confidence = min(confidence, 0.65)
            warnings.append(f"Evidence missing for {field_name}; confidence was capped.")
        if field_name in DATE_FIELDS and not _date_like(str(value)):
            warnings.append(f"Date parse warning for {field_name}: {value}.")

        valid.append({
            "field_name": field_name,
            "value": value,
            "evidence_text": evidence or f"Extracted {field_name}: {value}",
            "confidence": confidence,
            "source_document": document.get("filename"),
        })
    return valid, warnings


def _confidence(value) -> float:
    try:
        return max(0.0, min(float(value), 1.0))
    except (TypeError, ValueError):
        return 0.75


def _date_like(value: str) -> bool:
    if not value:
        return False
    for fmt in ("%Y-%m-%d", "%d %B %Y", "%d %b %Y"):
        try:
            datetime.strptime(value.strip(), fmt)
            return True
        except ValueError:
            pass
    return False
