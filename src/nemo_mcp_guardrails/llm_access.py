"""Shared interpretation of app model grants and approved configurations."""

import os
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.database.models import AppLlmGrantRecord, LlmConfigRecord
from nemo_mcp_guardrails.llm_credentials import LlmCredentialError, validate_llm_credential_reference
from nemo_mcp_guardrails.llm_security import LlmEndpointError, validate_llm_endpoint
from nemo_mcp_guardrails.llm_profiles import AZURE_PROVIDERS, SUPPORTED_PROVIDERS, validate_profile_metadata


from nemo_mcp_guardrails.model_credentials import require_owned_profile_scope, validate_owned_profile


LlmPurpose = Literal["main", "guardrail"]
LLM_SELECTION_FIELDS = {"main_llm_config_id": "main", "guardrail_llm_config_id": "guardrail"}


class LlmAccessError(RuntimeError):
    """Deny a model choice without revealing catalogue or credential metadata."""


def validate_llm_choice(config: LlmConfigRecord | None) -> None:
    """Validate a model bundle without reading its credential value."""

    if config is not None and (
        not config.enabled or config.provider.strip().lower() not in SUPPORTED_PROVIDERS
        or not config.model_name.strip()
    ):
        raise LlmAccessError("LLM selection is unavailable.")
    try:
        if config is not None and getattr(config, "owner_app_id", None) is not None:
            validate_owned_profile(config)
            return
        if config is not None and getattr(config, "encrypted_api_key", None) is not None:
            raise LlmCredentialError("App model ownership is unavailable.")
        if config is not None:
            validate_profile_metadata(config.provider, config.endpoint, config.credential_reference)
        if config is None or config.provider.strip().lower() in AZURE_PROVIDERS:
            validate_llm_endpoint(
                (config.endpoint if config else None) or os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            )
            validate_llm_credential_reference(config.credential_reference if config else None)
    except (LlmEndpointError, LlmCredentialError, ValueError) as error:
        raise LlmAccessError("LLM selection is unavailable.") from error



def require_llm_grant(
    db: Session, app_id: int, purpose: LlmPurpose, config_id: int | None,
) -> tuple[AppLlmGrantRecord, LlmConfigRecord | None]:
    """Require an enabled app/purpose grant, including for environment defaults."""

    grant = db.scalars(select(AppLlmGrantRecord).where(
        AppLlmGrantRecord.app_id == app_id, AppLlmGrantRecord.purpose == purpose,
        AppLlmGrantRecord.llm_config_id == config_id,
    )).one_or_none()
    if grant is None or not grant.enabled:
        raise LlmAccessError("LLM selection is unavailable.")
    config = db.get(LlmConfigRecord, config_id) if config_id is not None else None
    if config_id is not None and config is None:
        raise LlmAccessError("LLM selection is unavailable.")
    validate_llm_choice(config)
    try:
        require_owned_profile_scope(config, app_id, purpose)
    except LlmCredentialError as error:
        raise LlmAccessError("LLM selection is unavailable.") from error
    return grant, config
