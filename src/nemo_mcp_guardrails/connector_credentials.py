"""Backend-approved GitHub credential references and secret resolution."""

import os
import re


class ConnectorCredentialError(RuntimeError):
    """Reject connector credential configuration without exposing secret values."""


def validate_github_credential_reference(reference: str | None) -> str | None:
    """Allow the default PAT or an exact backend-approved environment name."""

    names = [
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        *os.getenv("GMS_ALLOWED_GITHUB_CREDENTIAL_ENV_VARS", "").split(","),
    ]
    allowed = {name.strip() for name in names if name.strip()}
    pattern = r"[A-Za-z_][A-Za-z0-9_]*"
    if any(re.fullmatch(pattern, name) is None for name in allowed):
        raise ConnectorCredentialError("GitHub credential approval configuration is invalid.")
    value = (reference or "").strip()
    if not value:
        return None
    if not value.startswith("env:"):
        raise ConnectorCredentialError("GitHub credentials require an approved env: reference.")
    name = value.removeprefix("env:").strip()
    if re.fullmatch(pattern, name) is None or name not in allowed:
        raise ConnectorCredentialError("GitHub credential reference is not approved.")
    return f"env:{name}"


def resolve_github_credential(reference: str | None) -> str:
    """Validate before reading a PAT; never resolve an arbitrary server secret."""

    approved = validate_github_credential_reference(reference)
    name = approved.removeprefix("env:") if approved else "GITHUB_PERSONAL_ACCESS_TOKEN"
    value = os.getenv(name)
    if not value:
        raise ConnectorCredentialError("GitHub credential is unavailable.")
    return value
