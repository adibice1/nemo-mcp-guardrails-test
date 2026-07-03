from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from fastapi.testclient import TestClient
from sqlalchemy import select
from _management_auth import install_management_admin_override

from nemo_mcp_guardrails.api.main import app
from nemo_mcp_guardrails.app_auth import hash_api_key
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import (
    AppConnectorRecord,
    AppRecord,
    ConnectorRecord,
)
from seed_normalized_policy_metadata import main as seed_normalized_metadata


TEMP_API_KEY = "temporary-connector-api-key"


def create_temporary_app() -> tuple[int, str]:
    """Create one temporary app for connector API checks."""

    suffix = uuid4().hex
    client_id = f"connector-api-{suffix}"
    with SessionLocal() as db:
        app_record = AppRecord(
            name=f"Temporary Connector App {suffix}",
            client_id=client_id,
            api_key_hash=hash_api_key(TEMP_API_KEY),
            authorized=True,
        )
        db.add(app_record)
        db.commit()
        db.refresh(app_record)

        return app_record.id, client_id


def delete_temporary_app(app_id: int) -> None:
    """Delete the temporary app created by this test."""

    with SessionLocal() as db:
        app_record = db.get(AppRecord, app_id)
        if app_record:
            db.delete(app_record)
            db.commit()


def github_connector_id() -> int:
    """Return the seeded GitHub connector ID."""

    with SessionLocal() as db:
        connector = db.scalar(
            select(ConnectorRecord).where(ConnectorRecord.name == "github")
        )
        assert connector is not None
        return connector.id


def count_app_connector_links(app_id: int) -> int:
    """Return connector-link count for one app."""

    with SessionLocal() as db:
        return len(
            list(
                db.scalars(
                    select(AppConnectorRecord).where(
                        AppConnectorRecord.app_id == app_id
                    )
                )
            )
        )


def main() -> None:
    """Verify app connector management APIs."""

    install_management_admin_override()
    seed_normalized_metadata()
    app_id, client_id = create_temporary_app()

    try:
        connector_id = github_connector_id()
        with TestClient(app) as client:
            create_by_id = client.post(
                f"/apps/{app_id}/connectors",
                json={
                    "connector_name": "github",
                    "credential_reference": "env:GITHUB_PERSONAL_ACCESS_TOKEN",
                    "enabled": True,
                },
            )
            assert create_by_id.status_code == 201, create_by_id.text
            create_body = create_by_id.json()
            assert create_body["app_id"] == app_id
            assert create_body["app_label"].startswith("Temporary Connector App")
            assert create_body["connector_id"] == connector_id
            assert create_body["connector_name"] == "github"
            assert create_body["connector_display_name"] == "GitHub"
            assert create_body["credential_reference"] == (
                "env:GITHUB_PERSONAL_ACCESS_TOKEN"
            )
            assert create_body["enabled"] is True
            assert create_body["connector_enabled"] is True
            assert count_app_connector_links(app_id) == 1

            list_by_id = client.get(f"/apps/{app_id}/connectors")
            assert list_by_id.status_code == 200, list_by_id.text
            assert len(list_by_id.json()) == 1

            update_by_name = client.put(
                f"/apps/{app_id}/connectors/github",
                json={
                    "credential_reference": "vault:github/test",
                    "enabled": False,
                },
            )
            assert update_by_name.status_code == 200, update_by_name.text
            assert update_by_name.json()["credential_reference"] == "vault:github/test"
            assert update_by_name.json()["enabled"] is False

            upsert_by_client_id = client.post(
                f"/apps/by-client-id/{client_id}/connectors",
                json={
                    "connector_id": connector_id,
                    "credential_reference": "env:GITHUB_PERSONAL_ACCESS_TOKEN",
                    "enabled": True,
                },
            )
            assert upsert_by_client_id.status_code == 201, upsert_by_client_id.text
            assert upsert_by_client_id.json()["connector_name"] == "github"
            assert upsert_by_client_id.json()["enabled"] is True
            assert count_app_connector_links(app_id) == 1

            list_by_client_id = client.get(
                f"/apps/by-client-id/{client_id}/connectors"
            )
            assert list_by_client_id.status_code == 200, list_by_client_id.text
            assert len(list_by_client_id.json()) == 1

            update_by_client_id = client.put(
                f"/apps/by-client-id/{client_id}/connectors/{connector_id}",
                json={"enabled": False},
            )
            assert update_by_client_id.status_code == 200, update_by_client_id.text
            assert update_by_client_id.json()["enabled"] is False

            missing_connector = client.post(
                f"/apps/{app_id}/connectors",
                json={"connector_name": "missing-connector", "enabled": True},
            )
            assert missing_connector.status_code == 404, missing_connector.text

            delete_by_client_id = client.delete(
                f"/apps/by-client-id/{client_id}/connectors/github"
            )
            assert delete_by_client_id.status_code == 204, delete_by_client_id.text
            assert count_app_connector_links(app_id) == 0

            delete_missing = client.delete(
                f"/apps/by-client-id/{client_id}/connectors/github"
            )
            assert delete_missing.status_code == 404, delete_missing.text

        print("App connector API checks passed.")
        print("- App connector links can be created by app ID.")
        print("- App connector links can be listed by app ID and client ID.")
        print("- Connector references work by name and numeric ID.")
        print("- Repeated POST updates the existing connector link.")
        print("- Connector links can be updated and deleted by client ID.")
        print("- Missing connector or missing app link returns 404.")

    finally:
        delete_temporary_app(app_id)


if __name__ == "__main__":
    main()
