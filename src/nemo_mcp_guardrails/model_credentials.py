"""Encrypt app-owned model keys with an independent backend-managed key."""

import hashlib
import json
import os
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from nemo_mcp_guardrails.llm_credentials import LlmCredentialError
from nemo_mcp_guardrails.llm_security import (
    validate_compatible_llm_endpoint, validate_llm_endpoint,
)


KEY_ENV = "GMS_MODEL_CREDENTIAL_ENCRYPTION_KEY"


def _cipher() -> Fernet:
    """Require a dedicated Fernet key; never derive it from another secret."""
    try:
        return Fernet(os.environ[KEY_ENV].encode("ascii"))
    except (KeyError, ValueError, UnicodeError) as error:
        raise LlmCredentialError("Model credential storage is unavailable.") from error


def credential_key_version() -> str:
    """Make encryption-key changes invalidate cached app runtimes."""
    return hashlib.sha256(os.getenv(KEY_ENV, "").encode("utf-8")).hexdigest()


def owned_profile_endpoint(provider: str, endpoint: str) -> str:
    """Keep the existing backend destination approvals for submitted model keys."""
    if provider == "openai_compatible":
        return validate_compatible_llm_endpoint(endpoint)
    if provider == "azure_openai":
        return validate_llm_endpoint(endpoint)
    raise ValueError("Unsupported app-owned model protocol.")


def validate_owned_profile(config: Any) -> str:
    """Reject mixed credential modes and recheck the current destination policy."""
    if (not isinstance(config.owner_app_id, int) or isinstance(config.owner_app_id, bool)
            or config.owner_app_id < 1 or not config.encrypted_api_key
            or config.credential_reference is not None or not config.endpoint):
        raise LlmCredentialError("App model credentials are unavailable.")
    return owned_profile_endpoint(config.provider, config.endpoint)


def require_owned_profile_scope(config: Any, app_id: int, purpose: str) -> None:
    """Allow an app-owned profile only as its owning app's main model."""
    owner = getattr(config, "owner_app_id", None)
    if owner is not None and (owner != app_id or purpose != "main"):
        raise LlmCredentialError("App model access is unavailable.")


def _context(app_id: int, provider: str, endpoint: str, model_name: str) -> list:
    """Bind encrypted bytes to their app, protocol, destination and model."""
    return [1, app_id, provider, endpoint, model_name]


def encrypt_model_key(api_key: str, *, app_id: int, provider: str,
                      endpoint: str, model_name: str) -> str:
    """Encrypt a submitted key without persisting plaintext or an env reference."""
    value = {"context": _context(app_id, provider, endpoint, model_name), "key": api_key}
    return _cipher().encrypt(json.dumps(value).encode("utf-8")).decode("ascii")


def decrypt_model_key(config: Any) -> str:
    """Reject ciphertext moved between app/profile contexts or encrypted by another key."""
    endpoint = validate_owned_profile(config)
    try:
        value = json.loads(_cipher().decrypt(config.encrypted_api_key.encode("ascii")))
        expected = _context(config.owner_app_id, config.provider, endpoint, config.model_name)
        if not isinstance(value, dict) or value.get("context") != expected:
            raise ValueError
        key = value.get("key")
        if (not isinstance(key, str) or not key.strip() or len(key) > 8192
                or any(ord(char) < 32 or ord(char) == 127 for char in key)):
            raise ValueError
        return key
    except (InvalidToken, ValueError, UnicodeError, TypeError, AttributeError) as error:
        raise LlmCredentialError("App model credentials are unavailable.") from error
