CIF_RISK_TRANSFER_POINT = "Loaded on board at port of loading"
CIF_UNSUPPORTED_MESSAGE = "This MVP focuses on CIF. Other Incoterms are not fully supported yet."
INCOTERM_MISSING_MESSAGE = "Incoterm is missing. CIF responsibility analysis cannot be completed."
CIF_NAMED_PLACE_MISSING_MESSAGE = "CIF named destination port is missing. Responsibility analysis may be incomplete."


CIF_SELLER_RESPONSIBILITIES = [
    "export clearance",
    "load goods on board",
    "arrange freight",
    "arrange insurance",
    "provide shipping and insurance documents",
    "meet LC shipment and presentation deadlines",
]

CIF_BUYER_RESPONSIBILITIES = [
    "bear risk after loading",
    "import clearance",
    "import duties",
    "destination port handling / delay exposure",
    "receive cargo",
]


def resolve_cif_responsibility(case: dict) -> dict:
    incoterm = str(case.get("incoterm") or "").strip().upper()
    named_place = str(case.get("incoterm_named_place") or "").strip()
    warnings: list[dict] = []

    if not incoterm:
        warnings.append({"code": "INCOTERM_MISSING", "message": INCOTERM_MISSING_MESSAGE})
        return _base_response(case, incoterm="", named_place=named_place, supported=False, warnings=warnings)

    if incoterm != "CIF":
        warnings.append({"code": "INCOTERM_NOT_FULLY_SUPPORTED", "message": CIF_UNSUPPORTED_MESSAGE})
        return _base_response(case, incoterm=incoterm, named_place=named_place, supported=False, warnings=warnings)

    if not named_place:
        warnings.append({"code": "CIF_NAMED_DESTINATION_PORT_MISSING", "message": CIF_NAMED_PLACE_MISSING_MESSAGE})

    response = _base_response(case, incoterm=incoterm, named_place=named_place, supported=True, warnings=warnings)
    response.update(
        {
            "risk_transfer_point": CIF_RISK_TRANSFER_POINT,
            "seller_responsibilities": CIF_SELLER_RESPONSIBILITIES,
            "buyer_responsibilities": CIF_BUYER_RESPONSIBILITIES,
            "cost_responsibility": {
                "main_carriage": "SELLER",
                "cargo_insurance": "SELLER",
                "import_clearance": "BUYER",
                "import_duties_and_taxes": "BUYER",
                "post_arrival_operational_costs": "BUYER",
            },
        }
    )
    return response


def _base_response(case: dict, incoterm: str, named_place: str, supported: bool, warnings: list[dict]) -> dict:
    return {
        "case_id": case.get("case_id"),
        "incoterm": incoterm,
        "incoterm_basis": "CIF" if incoterm == "CIF" else incoterm,
        "named_destination_port": named_place,
        "supported": supported,
        "risk_transfer_point": "",
        "seller_responsibilities": [],
        "buyer_responsibilities": [],
        "cost_responsibility": {},
        "warnings": warnings,
    }
