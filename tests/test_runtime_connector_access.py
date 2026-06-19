from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import select

from nemo_mcp_guardrails.app_auth import hash_api_key
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import (
    AppConnectorRecord,
    AppRecord,
    ConnectorRecord,
)
from nemo_mcp_guardrails.runtime_factory import (
    ConnectorAccessError,
    require_app_connector_access,
)
from seed_normalized_policy_metadata import main as seed_normalized_metadata


TEMP_API_KEY = "temporary-runtime-connector-access-key"


def create_temporary_records() -> tuple[int, int, int]:
    """Create linked, unlinked, and disabled-link apps for access checks."""

    seed_normalized_metadata()
    suffix = uuid4().hex

    with SessionLocal() as db:
        github_connector = db.scalar(
            select(ConnectorRecord).where(ConnectorRecord.name == "github")
        )
        assert github_connector is not None

        linked_app = AppRecord(
            name=f"Temporary Connector Linked App {suffix}",
            client_id=f"connector-linked-{suffix}",
            api_key_hash=hash_api_key(TEMP_API_KEY),
            authorized=True,
        )
        unlinked_app = AppRecord(
            name=f"Temporary Connector Unlinked App {suffix}",
            client_id=f"connector-unlinked-{suffix}",
            api_key_hash=hash_api_key(TEMP_API_KEY),
            authorized=True,
        )
        disabled_link_app = AppRecord(
            name=f"Temporary Connector Disabled App {suffix}",
            client_id=f"connector-disabled-{suffix}",
            api_key_hash=hash_api_key(TEMP_API_KEY),
            authorized=True,
        )
        db.add_all([linked_app, unlinked_app, disabled_link_app])
        db.flush()

        db.add_all(
            [
                AppConnectorRecord(
                    app_id=linked_app.id,
                    connector_id=github_connector.id,
                    enabled=True,
                ),
                AppConnectorRecord(
                    app_id=disabled_link_app.id,
                    connector_id=github_connector.id,
                    enabled=False,
                ),
            ]
        )
        db.commit()

        return linked_app.id, unlinked_app.id, disabled_link_app.id


def delete_temporary_apps(app_ids: tuple[int, ...]) -> None:
    """Delete temporary apps and cascaded connector links."""

    with SessionLocal() as db:
        for app_id in app_ids:
            app_record = db.get(AppRecord, app_id)
            if app_record:
                db.delete(app_record)
        db.commit()


def assert_connector_denied(app_id: int) -> None:
    """Assert that connector access fails for one app."""

    try:
        require_app_connector_access(app_id, "github")
    except ConnectorAccessError as error:
        assert "not linked to enabled connector: github" in str(error)
    else:
        raise AssertionError("Connector access should have been denied")


def main() -> None:
    """Verify runtime connector access is enforced before MCP construction."""

    linked_app_id, unlinked_app_id, disabled_link_app_id = create_temporary_records()

    try:
        require_app_connector_access(linked_app_id, "github")
        assert_connector_denied(unlinked_app_id)
        assert_connector_denied(disabled_link_app_id)

        print("Runtime connector access checks passed.")
        print("- App linked to enabled GitHub connector was allowed.")
        print("- App without GitHub connector link was rejected.")
        print("- App with disabled GitHub connector link was rejected.")

    finally:
        delete_temporary_apps(
            (linked_app_id, unlinked_app_id, disabled_link_app_id)
        )
        print("- Temporary connector-access apps deleted")


if __name__ == "__main__":
    main()
