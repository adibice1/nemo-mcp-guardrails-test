import atexit
from uuid import uuid4

from nemo_mcp_guardrails.api.main import app
from nemo_mcp_guardrails.api.management_auth import require_management_user
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import UserRecord
from nemo_mcp_guardrails.management_auth import hash_password


def install_management_admin_override() -> None:
    """Install a temporary admin dependency for non-RBAC API diagnostics."""

    email = f"api-test-admin-{uuid4().hex}@example.com"
    with SessionLocal() as db:
        user = UserRecord(
            email=email,
            name="API Test Admin",
            username=email,
            password_hash=hash_password("test-password"),
            system_role="admin",
            enabled=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id
        db.expunge(user)

    app.dependency_overrides[require_management_user] = lambda: user
    cleaned = False

    def cleanup() -> None:
        nonlocal cleaned
        if cleaned:
            return
        cleaned = True
        app.dependency_overrides.pop(require_management_user, None)
        with SessionLocal() as db:
            persisted = db.get(UserRecord, user_id)
            if persisted is not None:
                db.delete(persisted)
                db.commit()

    atexit.register(cleanup)
