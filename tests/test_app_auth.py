from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from nemo_mcp_guardrails.app_auth import authenticate_app, hash_api_key
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import AppRecord


VALID_API_KEY = "temporary-valid-api-key"


def create_temporary_apps() -> tuple[int, int, str]:
    """Create authorized and unauthorized temporary apps."""

    suffix = uuid4().hex
    authorized_client_id = f"auth-test-authorized-{suffix}"

    with SessionLocal() as db:
        authorized_app = AppRecord(
            name="Temporary Authorized App",
            client_id=authorized_client_id,
            api_key_hash=hash_api_key(VALID_API_KEY),
            authorized=True,
        )
        unauthorized_app = AppRecord(
            name="Temporary Unauthorized App",
            client_id=f"auth-test-unauthorized-{suffix}",
            api_key_hash=hash_api_key(VALID_API_KEY),
            authorized=False,
        )
        db.add_all([authorized_app, unauthorized_app])
        db.commit()
        db.refresh(authorized_app)
        db.refresh(unauthorized_app)

        return authorized_app.id, unauthorized_app.id, authorized_client_id


def delete_temporary_apps(app_ids: tuple[int, int]) -> None:
    """Delete temporary authentication-test apps."""

    with SessionLocal() as db:
        for app_id in app_ids:
            app = db.get(AppRecord, app_id)
            if app:
                db.delete(app)
        db.commit()


def main() -> None:
    """Verify valid, wrong-key, unknown, and unauthorized app authentication."""

    authorized_id, unauthorized_id, client_id = create_temporary_apps()

    try:
        with SessionLocal() as db:
            valid_app = authenticate_app(db, client_id, VALID_API_KEY)
            wrong_key_app = authenticate_app(db, client_id, "wrong-api-key")
            unknown_app = authenticate_app(
                db,
                "unknown-client-id",
                VALID_API_KEY,
            )
            unauthorized_app = db.get(AppRecord, unauthorized_id)
            assert unauthorized_app is not None
            unauthorized_result = authenticate_app(
                db,
                unauthorized_app.client_id,
                VALID_API_KEY,
            )

            assert valid_app is not None
            assert valid_app.id == authorized_id
            assert wrong_key_app is None
            assert unknown_app is None
            assert unauthorized_result is None

        print("App authentication checks passed.")
        print("- Valid authorized app accepted")
        print("- Wrong API key rejected")
        print("- Unknown client ID rejected")
        print("- Unauthorized app rejected")
    finally:
        delete_temporary_apps((authorized_id, unauthorized_id))
        print("- Temporary authentication-test apps deleted")


if __name__ == "__main__":
    main()
