def extract_with_openai_file(document: dict) -> dict:
    return {
        "status": "UNSUPPORTED",
        "fields": [],
        "warnings": [],
        "errors": [{
            "code": "OPENAI_FILE_NOT_IMPLEMENTED",
            "message": "OpenAI file extraction is an optional mode and is not enabled in this build.",
        }],
        "openai_file_used": False,
    }
