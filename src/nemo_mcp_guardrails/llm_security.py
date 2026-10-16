"""Backend-controlled destinations for Azure LLM credentials."""

import os
from urllib.parse import urlsplit


class LlmEndpointError(RuntimeError):
    """Reject an unsafe or unapproved LLM destination without exposing its value."""


def _https_origin(value: str) -> str:
    """Normalize an HTTPS origin without accepting embedded credentials or paths."""

    value = value.strip()
    try:
        parts = urlsplit(value)
        port = parts.port
        if (
            parts.scheme != "https"
            or not parts.hostname
            or parts.username is not None
            or parts.password is not None
            or parts.path not in {"", "/"}
            or parts.query
            or parts.fragment
            or "\\" in value
            or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value)
        ):
            raise ValueError
        host = parts.hostname.encode("idna").decode("ascii").lower()
        authority = f"[{host}]" if ":" in host else host
        if port is not None and port != 443:
            authority += f":{port}"
        return f"https://{authority}"
    except (ValueError, UnicodeError) as error:
        raise LlmEndpointError(
            "LLM endpoints must be HTTPS origins without credentials, paths, queries, or fragments."
        ) from error


def validate_llm_endpoint(endpoint: str, *, default_endpoint: str | None = None) -> str:
    """Require the default Azure origin or an exact backend-approved HTTPS origin."""

    origin = _https_origin(endpoint)
    default = (
        default_endpoint if default_endpoint is not None
        else os.getenv("AZURE_OPENAI_ENDPOINT", "")
    )
    configured = [default, *os.getenv("GMS_ALLOWED_LLM_ENDPOINTS", "").split(",")]
    approved = {_https_origin(value) for value in configured if value.strip()}
    if origin not in approved:
        raise LlmEndpointError("LLM endpoint is not approved by backend configuration.")
    return origin
