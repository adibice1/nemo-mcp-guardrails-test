"""Backend-approved environment names for LLM credential provisioning."""

import os
import re


class LlmCredentialError(RuntimeError):
    """Reject an unapproved credential reference without exposing its value."""


def validate_llm_credential_reference(reference: str | None) -> str | None:
    """Approve the default Azure key or an exact backend-configured env name."""

    names = ["AZURE_OPENAI_API_KEY", *os.getenv("GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS", "").split(",")]
    allowed = {name.strip() for name in names if name.strip()}
    pattern = r"[A-Za-z_][A-Za-z0-9_]*"
    if any(re.fullmatch(pattern, name) is None for name in allowed):
        raise LlmCredentialError("LLM credential approval configuration is invalid.")
    value = (reference or "").strip()
    if not value:
        return None
    if not value.startswith("env:"):
        raise LlmCredentialError("LLM credentials require an approved env: reference.")
    name = value.removeprefix("env:").strip()
    if re.fullmatch(pattern, name) is None or name not in allowed:
        raise LlmCredentialError("LLM credential reference is not approved.")
    return f"env:{name}"


def resolve_llm_credential(reference: str) -> str:
    """Validate a reference before reading its approved credential value."""

    approved = validate_llm_credential_reference(reference)
    name = approved.removeprefix("env:") if approved else "AZURE_OPENAI_API_KEY"
    value = os.getenv(name)
    if not value:
        raise LlmCredentialError("LLM credential is unavailable.")
    return value
