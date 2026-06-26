import os


def extract_with_vision_pages(document: dict, reason_code: str = "SCANNED_PDF_UNSUPPORTED") -> dict:
    if os.getenv("VISION_EXTRACTION_ENABLED", "false").lower() != "true":
        return {
            "status": "NEEDS_VISION",
            "fields": [],
            "warnings": ["Document appears to be scanned or image-based."],
            "errors": [{
                "code": reason_code,
                "message": "This appears to be a scanned PDF. Enable VISION_EXTRACTION_ENABLED to process it.",
            }],
            "vision_used": False,
        }
    return {
        "status": "UNSUPPORTED",
        "fields": [],
        "warnings": [],
        "errors": [{
            "code": "VISION_NOT_IMPLEMENTED",
            "message": "Vision pages extraction is not implemented yet.",
        }],
        "vision_used": False,
    }
