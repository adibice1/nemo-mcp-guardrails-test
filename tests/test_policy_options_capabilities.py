"""Offline HTTP checks for enabled, executable policy-authoring options."""

import os
from unittest.mock import patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Use real metadata and JWT authentication with disposable SQLite."""

    with patch.dict(os.environ, {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "GMS_JWT_SECRET": "policy-options-test-secret-at-least-32-characters",
    }):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from nemo_mcp_guardrails.api import policy_metadata
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database import models
        from nemo_mcp_guardrails.management_auth import create_access_token
        from nemo_mcp_guardrails.policy_compiler import GITHUB_METADATA_TOOL_MAPPINGS, GITHUB_WRITE_TOOL_MAPPINGS

        engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        for model in (models.UserRecord, models.ConnectorRecord, models.ConnectorActionRecord,
                      models.ConnectorResourceRecord, models.ConnectorToolMappingRecord):
            model.__table__.create(engine)
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        with sessions.begin() as db:
            user = models.UserRecord(name="Developer", username="developer", email="developer@example.invalid",
                                     password_hash="unused", system_role="developer", enabled=True)
            github = models.ConnectorRecord(name="github", display_name="GitHub")
            sharepoint = models.ConnectorRecord(name="sharepoint", display_name="SharePoint")
            db.add_all([user, github, sharepoint])
            db.flush()
            headers = {"Authorization": "Bearer " + create_access_token(user)}
            actions = {name: models.ConnectorActionRecord(connector_id=github.id, name=name, display_name=name)
                       for name in {action for action, _ in GITHUB_METADATA_TOOL_MAPPINGS}}
            resources = {name: models.ConnectorResourceRecord(connector_id=github.id, name=name, display_name=name)
                         for name in {resource for _, resource in GITHUB_METADATA_TOOL_MAPPINGS}}
            db.add_all([*actions.values(), *resources.values()])
            db.flush()
            mappings = []
            for (action, resource), tools in GITHUB_METADATA_TOOL_MAPPINGS.items():
                for tool in tools:
                    mapping = models.ConnectorToolMappingRecord(connector_id=github.id,
                        action_id=actions[action].id, resource_id=resources[resource].id, tool_name=tool)
                    db.add(mapping)
                    mappings.append(mapping)
            db.add(models.ConnectorToolMappingRecord(connector_id=github.id,
                action_id=actions["delete"].id, resource_id=resources["branch"].id, tool_name="unreviewed_delete_branch"))
            other_action = models.ConnectorActionRecord(connector_id=sharepoint.id, name="create", display_name="Create")
            other_resource = models.ConnectorResourceRecord(connector_id=sharepoint.id, name="issue", display_name="Issue")
            db.add_all([other_action, other_resource])
            db.flush()
            db.add(models.ConnectorToolMappingRecord(connector_id=sharepoint.id,
                action_id=other_action.id, resource_id=other_resource.id, tool_name="unreviewed_create_issue"))
            db.add_all([
                models.ConnectorToolMappingRecord(connector_id=github.id, action_id=other_action.id,
                    resource_id=resources["issue"].id, tool_name="mismatched_action"),
                models.ConnectorToolMappingRecord(connector_id=github.id, action_id=actions["create"].id,
                    resource_id=other_resource.id, tool_name="mismatched_resource"),
            ])
            db.flush()
            controls = [(models.ConnectorRecord, github.id),
                        (models.ConnectorActionRecord, actions["create"].id),
                        (models.ConnectorResourceRecord, resources["issue"].id),
                        (models.ConnectorToolMappingRecord, next(m.id for m in mappings
                         if m.action_id == actions["create"].id and m.resource_id == resources["issue"].id))]

        def test_db():
            """Provide fresh sessions for real authentication and catalogue reads."""

            with sessions() as db:
                yield db

        app = FastAPI()
        app.include_router(policy_metadata.router)
        app.dependency_overrides[get_db] = test_db

        def options(client):
            """Flatten the authenticated HTTP response without duplicating resources."""

            response = client.get("/policy-options", headers=headers)
            assert response.status_code == 200, response.text
            result = {}
            for connector in response.json():
                for action in connector["actions"]:
                    for resource in action["resources"]:
                        key = (connector["value"], action["value"], resource["value"])
                        assert key not in result
                        result[key] = resource["condition_fields"]
            return result

        with TestClient(app) as client:
            assert client.get("/policy-options").status_code == 401
            assert client.get("/policy-options", headers={"Authorization": "Bearer invalid"}).status_code == 401
            actual = options(client)
            assert set(actual) == {("github", action, resource) for action, resource in GITHUB_WRITE_TOOL_MAPPINGS}
            assert actual[("github", "create", "pull_request")] == ["title", "source_branch", "target_branch"]
            assert actual[("github", "merge", "pull_request")] == ["number", "source_branch", "target_branch"]
            assert actual[("github", "create", "branch")] == []
            assert actual[("github", "push", "file")] == ["path"]
            assert actual[("github", "delete", "file")] == ["path"]
            for model, record_id in controls:
                with sessions.begin() as db:
                    db.get(model, record_id).enabled = False
                assert ("github", "create", "issue") not in options(client)
                with sessions.begin() as db:
                    db.get(model, record_id).enabled = True
                assert options(client) == actual
        engine.dispose()
    print("Policy options passed: JWT, enabled flags, supported writes, excluded reads/connectors and selector fields.")


if __name__ == "__main__":
    main()
