import json

from app.services import llm_provider


class StructuredLLMError(RuntimeError):
    code = "LLM_GENERATION_FAILED"


def generate_structured(*, purpose: str, timeout_seconds: int, schema_name: str, schema: dict, instructions: str, input_data: dict) -> dict:
    if not llm_provider.api_key():
        raise StructuredLLMError(f"{llm_provider.provider_label()} API key is not configured.")

    messages = [
        {
            "role": "system",
            "content": (
                f"{instructions} Return only a JSON object named {schema_name}. "
                "The object must match the supplied JSON schema. Do not wrap the JSON in markdown."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "json_schema": schema,
                    "input": input_data,
                },
                ensure_ascii=False,
            ),
        },
    ]
    try:
        text = llm_provider.chat_completion(
            messages=messages,
            purpose=purpose,
            temperature=0,
            response_format={"type": "json_object"},
            timeout=timeout_seconds,
        )
    except Exception as error:
        raise StructuredLLMError(f"{llm_provider.provider_label()} request failed: {error}") from error

    if not text or not text.strip():
        raise StructuredLLMError(f"{llm_provider.provider_label()} returned no structured output.")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as error:
        raise StructuredLLMError(f"{llm_provider.provider_label()} returned invalid JSON.") from error
    if not isinstance(parsed, dict):
        raise StructuredLLMError(f"{llm_provider.provider_label()} structured output must be a JSON object.")
    return parsed
