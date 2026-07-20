"""Central LLM provider resolution and a unified chat-completion entrypoint.

ForeSail's optional LLM features (document field extraction, agent run
summary, relevance-factor and news-event extraction) all run against a single
configurable provider through the same chat/completions request shape.

Google Gemini is the default provider. Gemini is reached through its
OpenAI-compatible endpoint, so every call site keeps an identical request body
and only the base URL, key, and model name change.

``chat_completion`` sends the primary provider first. OpenAI fallback is
available only when explicitly enabled. Call sites keep their own parsing and
deterministic fallbacks.
"""

import json
import os
import urllib.error
import urllib.request

GEMINI_DEFAULT_MODEL = "gemini-2.0-flash"
GEMINI_DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"

_OPENAI_MODEL_DEFAULTS = {
    "summary": "gpt-4.1-mini",
    "extraction": "gpt-4o-mini",
    "relevance": "gpt-4o-mini",
    "event_extraction": "gpt-4o-mini",
    "action": "gpt-4o-mini",
    "plan": "gpt-4o-mini",
}
_OPENAI_MODEL_ENV = {
    "summary": "OPENAI_SUMMARY_MODEL",
    "extraction": "OPENAI_EXTRACTION_MODEL",
    "relevance": "OPENAI_RELEVANCE_FACTOR_MODEL",
    "event_extraction": "OPENAI_EVENT_EXTRACTION_MODEL",
    "action": "OPENAI_ACTION_MODEL",
    "plan": "OPENAI_PLAN_MODEL",
}
_GEMINI_MODEL_ENV = {
    "summary": "GEMINI_SUMMARY_MODEL",
    "extraction": "GEMINI_EXTRACTION_MODEL",
    "relevance": "GEMINI_RELEVANCE_FACTOR_MODEL",
    "event_extraction": "GEMINI_EVENT_EXTRACTION_MODEL",
    "action": "GEMINI_ACTION_MODEL",
    "plan": "GEMINI_PLAN_MODEL",
}


class LLMError(RuntimeError):
    """Raised when no configured provider could return a completion."""


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _gemini_key() -> str:
    return (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()


def _openai_key() -> str:
    return (os.getenv("OPENAI_API_KEY") or "").strip()


def provider() -> str:
    explicit = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    if explicit in {"gemini", "google"}:
        return "gemini"
    if explicit == "openai":
        return "openai"
    return "gemini"


def _key_for(prov: str) -> str:
    return _gemini_key() if prov == "gemini" else _openai_key()


def _url_for(prov: str) -> str:
    if prov == "gemini":
        base = os.getenv("GEMINI_BASE_URL", GEMINI_DEFAULT_BASE_URL).rstrip("/")
        return f"{base}/chat/completions"
    return "https://api.openai.com/v1/chat/completions"


def _model_for(prov: str, purpose: str) -> str:
    if prov == "gemini":
        return os.getenv(_GEMINI_MODEL_ENV[purpose], os.getenv("GEMINI_MODEL", GEMINI_DEFAULT_MODEL))
    return os.getenv(_OPENAI_MODEL_ENV[purpose], _OPENAI_MODEL_DEFAULTS[purpose])


def api_key() -> str:
    return _key_for(provider())


def chat_completions_url() -> str:
    return _url_for(provider())


def model_for(purpose: str) -> str:
    return _model_for(provider(), purpose)


def provider_label() -> str:
    return "Google Gemini" if provider() == "gemini" else "OpenAI"


def _provider_chain() -> list[str]:
    primary = provider()
    chain = [primary]
    if not _truthy(os.getenv("LLM_FALLBACK_ENABLED", "false")):
        return chain
    fallback = "openai" if primary == "gemini" else "gemini"
    if _key_for(fallback):
        chain.append(fallback)
    return chain


def chat_completion(
    *,
    messages: list[dict],
    purpose: str,
    temperature: float = 0.0,
    response_format: dict | None = None,
    timeout: int = 60,
) -> str:
    """Return the assistant message content, trying the primary provider then
    falling back to the other configured provider on failure."""
    last_error: Exception | None = None
    for prov in _provider_chain():
        key = _key_for(prov)
        if not key:
            continue
        body: dict = {"model": _model_for(prov, purpose), "messages": messages, "temperature": temperature}
        if response_format is not None:
            body["response_format"] = response_format
        request = urllib.request.Request(
            _url_for(prov),
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            if isinstance(content, str) and content.strip():
                return content
            last_error = LLMError(f"{prov} returned empty content")
        except Exception as error:  # noqa: BLE001 - try the next provider
            last_error = error
            continue
    raise LLMError("no LLM provider returned a completion") from last_error
