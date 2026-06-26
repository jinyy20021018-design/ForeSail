def extract_with_openai_file(document: dict) -> dict:
    return {
        "status": "UNSUPPORTED",
        "fields": [],
        "warnings": [],
        "errors": [{
            "code": "OPENAI_FILE_NOT_IMPLEMENTED",
            "message": "OpenAI file extraction mode is not implemented yet.",
        }],
        "openai_file_used": False,
    }
