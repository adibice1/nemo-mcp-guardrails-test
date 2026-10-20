"""Backend-controlled destinations for Azure and compatible LLM credentials."""

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


def _compatible_base_url(value: str) -> str:
    """Normalize a base URL, allowing HTTP only for explicit literal loopback hosts."""

    try:
        if not value or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError
        parts = urlsplit(value)
        port = parts.port
        if (not parts.hostname or parts.scheme not in {"https", "http"}
                or parts.username is not None or parts.password is not None
                or parts.query or parts.fragment or "\\" in value):
            raise ValueError
        host = parts.hostname.encode("idna").decode("ascii").lower()
        if parts.scheme == "http" and host not in {"127.0.0.1", "::1"}:
            raise ValueError
        path = parts.path.rstrip("/")
        if path and (not path.startswith("/") or any(
            not segment or segment in {".", ".."}
            or any(not (char.isascii() and (char.isalnum() or char in "_-.") ) for char in segment)
            for segment in path[1:].split("/")
        )):
            raise ValueError
        authority = f"[{host}]" if ":" in host else host
        if port is not None and port != (443 if parts.scheme == "https" else 80):
            authority += f":{port}"
        return f"{parts.scheme}://{authority}{path}"
    except (ValueError, UnicodeError) as error:
        raise LlmEndpointError("Invalid compatible LLM base URL.") from error


def validate_compatible_llm_endpoint(endpoint: str) -> str:
    """Require an exact backend-approved compatible base URL, including its path."""

    base_url = _compatible_base_url(endpoint)
    configured = os.getenv("GMS_ALLOWED_COMPATIBLE_LLM_ENDPOINTS", "").split(",")
    approved = {_compatible_base_url(value.strip()) for value in configured if value.strip()}
    if base_url not in approved:
        raise LlmEndpointError("Compatible LLM endpoint is not approved by backend configuration.")
    return base_url
