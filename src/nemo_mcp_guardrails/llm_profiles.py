"""Shared protocol validation for stored runtime and backend authoring profiles."""

from nemo_mcp_guardrails.llm_credentials import LlmCredentialError, validate_llm_credential_reference
from nemo_mcp_guardrails.llm_security import validate_compatible_llm_endpoint, validate_llm_endpoint


AZURE_PROVIDERS = frozenset({"azure", "azure_openai"})
COMPATIBLE_PROVIDER = "openai_compatible"
SUPPORTED_PROVIDERS = AZURE_PROVIDERS | {COMPATIBLE_PROVIDER}


def validate_profile_metadata(
    provider: str, endpoint: str | None, credential_reference: str | None,
) -> tuple[str | None, str | None]:
    """Validate protocol-specific metadata without reading any credential value."""

    provider = provider.strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError("Unsupported LLM API protocol.")
    if provider == COMPATIBLE_PROVIDER:
        normalized = validate_compatible_llm_endpoint(endpoint or "")
        reference = validate_llm_credential_reference(credential_reference)
        if reference is None:
            raise LlmCredentialError("Compatible LLMs require an explicit approved credential reference.")
        return normalized, reference
    normalized = validate_llm_endpoint(endpoint) if endpoint else None
    return normalized, validate_llm_credential_reference(credential_reference)
