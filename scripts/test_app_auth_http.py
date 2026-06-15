from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from fastapi.testclient import TestClient

from nemo_mcp_guardrails.api.main import app
from nemo_mcp_guardrails.app_auth import hash_api_key
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import AppRecord


VALID_API_KEY = "temporary-valid-http-api-key"
INVALID_RESPONSE = {"detail": "Invalid app credentials"}


def create_temporary_apps() -> tuple[int, int, str, str]:
    """Create authorized and unauthorized temporary HTTP-test apps."""

    suffix = uuid4().hex
    authorized_client_id = f"http-auth-authorized-{suffix}"
    unauthorized_client_id = f"http-auth-unauthorized-{suffix}"

    with SessionLocal() as db:
        authorized_app = AppRecord(
            name="Temporary HTTP Authorized App",
            client_id=authorized_client_id,
            api_key_hash=hash_api_key(VALID_API_KEY),
            authorized=True,
        )
        unauthorized_app = AppRecord(
            name="Temporary HTTP Unauthorized App",
            client_id=unauthorized_client_id,
            api_key_hash=hash_api_key(VALID_API_KEY),
            authorized=False,
        )
        db.add_all([authorized_app, unauthorized_app])
        db.commit()
        db.refresh(authorized_app)
        db.refresh(unauthorized_app)

        return (
            authorized_app.id,
            unauthorized_app.id,
            authorized_client_id,
            unauthorized_client_id,
        )


def delete_temporary_apps(app_ids: tuple[int, int]) -> None:
    """Delete temporary HTTP authentication-test apps."""

    with SessionLocal() as db:
        for app_id in app_ids:
            app_record = db.get(AppRecord, app_id)
            if app_record:
                db.delete(app_record)
        db.commit()


def main() -> None:
    """Verify the HTTP authentication boundary accepts and rejects correctly."""

    authorized_id, unauthorized_id, client_id, unauthorized_client_id = (
        create_temporary_apps()
    )

    try:
        with TestClient(app) as client:
            missing = client.get("/v1/guardrails/auth-check")
            wrong_key = client.get(
                "/v1/guardrails/auth-check",
                headers={
                    "X-App-ID": client_id,
                    "X-API-Key": "wrong-api-key",
                },
            )
            unknown = client.get(
                "/v1/guardrails/auth-check",
                headers={
                    "X-App-ID": "unknown-client-id",
                    "X-API-Key": VALID_API_KEY,
                },
            )
            unauthorized = client.get(
                "/v1/guardrails/auth-check",
                headers={
                    "X-App-ID": unauthorized_client_id,
                    "X-API-Key": VALID_API_KEY,
                },
            )
            valid = client.get(
                "/v1/guardrails/auth-check",
                headers={
                    "X-App-ID": client_id,
                    "X-API-Key": VALID_API_KEY,
                },
            )
            run_missing = client.post(
                "/v1/guardrails/run",
                json={"message": "Summarize the repository."},
            )
            run_valid = client.post(
                "/v1/guardrails/run",
                headers={
                    "X-App-ID": client_id,
                    "X-API-Key": VALID_API_KEY,
                },
                json={"message": "Summarize the repository."},
            )

        for response in (missing, wrong_key, unknown, unauthorized, run_missing):
            assert response.status_code == 401
            assert response.json() == INVALID_RESPONSE

        assert valid.status_code == 200
        assert valid.json() == {
            "status": "authenticated",
            "app_id": authorized_id,
            "client_id": client_id,
        }
        assert run_valid.status_code == 200
        run_context = run_valid.json()
        assert run_context["status"] == "context_ready"
        assert run_context["app_id"] == authorized_id
        assert run_context["client_id"] == client_id
        assert run_context["input_policy_count"] == 0
        assert run_context["input_rule_count"] == 0
        assert run_context["output_rule_count"] >= 1
        assert run_context["blocked_tools"] == []

        print("HTTP app authentication checks passed.")
        print("- Missing headers rejected")
        print("- Wrong API key rejected")
        print("- Unknown client ID rejected")
        print("- Unauthorized app rejected")
        print("- Valid authorized app accepted")
        print("- Authenticated app-scoped runtime context prepared")
    finally:
        delete_temporary_apps((authorized_id, unauthorized_id))
        print("- Temporary HTTP authentication-test apps deleted")


if __name__ == "__main__":
    main()
