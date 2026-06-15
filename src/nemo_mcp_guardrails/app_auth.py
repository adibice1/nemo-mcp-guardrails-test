import hashlib
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.database.models import AppRecord


def hash_api_key(api_key: str) -> str:
    """Hash one client-app API key for persistence or comparison."""

    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def verify_api_key(api_key: str, expected_hash: str) -> bool:
    """Compare an API key with its stored hash using constant-time comparison."""

    return secrets.compare_digest(hash_api_key(api_key), expected_hash)


def authenticate_app(
    db: Session,
    client_id: str,
    api_key: str,
) -> AppRecord | None:
    """Return an authorized app only when its client ID and API key match."""

    app = db.scalar(select(AppRecord).where(AppRecord.client_id == client_id))
    if not app or not app.authorized:
        return None

    if not verify_api_key(api_key, app.api_key_hash):
        return None

    return app
