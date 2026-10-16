"""Offline HTTP checks for versioned selectors and assignment-safe identities."""

import os
from unittest.mock import patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Use real JWT/RBAC and disposable SQLite without model or connector calls."""

    with patch.dict(os.environ, {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "GMS_JWT_SECRET": "condition-storage-test-secret-at-least-32-characters",
    }):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sqlalchemy import JSON, MetaData, create_engine, select
        from sqlalchemy.dialects.postgresql import JSONB
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from nemo_mcp_guardrails.api import policies, policy_assignment_resolution
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database import models
        from nemo_mcp_guardrails.management_auth import create_access_token
        from nemo_mcp_guardrails.policy_service import consolidate_equivalent_policies
        from inventory_resource_conditions import inventory

        engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        metadata = MetaData()
        for table in models.Base.metadata.sorted_tables:
            cloned = table.to_metadata(metadata)
            for column in cloned.columns:
                if isinstance(column.type, JSONB):
                    column.type = JSON()
                    column.server_default = None
        metadata.create_all(engine)
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        with sessions.begin() as db:
            github = models.ConnectorRecord(name="github", display_name="GitHub")
            db.add_all([github, models.ConnectorRecord(name="global", display_name="Global")])
            db.flush()
            actions = {name: models.ConnectorActionRecord(connector_id=github.id, name=name, display_name=name)
                       for name in ("create", "delete", "merge", "update")}
            resources = {name: models.ConnectorResourceRecord(connector_id=github.id, name=name, display_name=name)
                         for name in ("issue", "file", "pull_request")}
            db.add_all([*actions.values(), *resources.values()])
            db.flush()
            for action, resource, tool in (("create", "issue", "issue_write"), ("create", "pull_request", "create_pull_request"), ("delete", "file", "delete_file"),
                                           ("merge", "pull_request", "merge_pull_request"), ("update", "issue", "issue_write")):
                db.add(models.ConnectorToolMappingRecord(connector_id=github.id, action_id=actions[action].id,
                                                        resource_id=resources[resource].id, tool_name=tool))
            headers = {}
            users = {}
            for name, role in (("admin", "admin"), ("developer", "developer")):
                user = models.UserRecord(name=name, username=name, email=f"{name}@example.invalid",
                                         password_hash="unused", system_role=role, enabled=True)
                db.add(user)
                db.flush()
                users[name] = user.id
                headers[name] = {"Authorization": "Bearer " + create_access_token(user)}
            db.add_all([models.AppRecord(id=i, client_id=f"app-{i}", name=f"App {i}", api_key_hash="unused") for i in (1, 2)])
            db.flush()
            db.add(models.AppUserRecord(app_id=1, user_id=users["developer"], role="admin"))
            legacy_ids = []
            for index in range(2):
                legacy = models.PolicyRecord(policy_type="input", connector="github", action="create", resource="issue",
                                             connector_id=github.id, action_id=actions["create"].id,
                                             resource_id=resources["issue"].id, conditions={"custom_resource": "legacy"})
                db.add(legacy)
                db.flush()
                legacy_ids.append(legacy.id)
            legacy_assignments = []
            for app_id in (1, 2):
                assignment = models.AppPolicyAssignmentRecord(app_id=app_id, policy_id=legacy_ids[0], display_name=f"App {app_id} legacy")
                db.add(assignment)
                db.flush()
                legacy_assignments.append(assignment.id)

        def test_db():
            """Keep authentication and service behavior real while isolating persistence."""

            with sessions() as db:
                yield db

        app = FastAPI()
        app.include_router(policies.router)
        app.include_router(policy_assignment_resolution.router)
        app.dependency_overrides[get_db] = test_db
        payload = {"policy_type": "input", "connector": "github", "action": "create", "resource": "issue",
                   "conditions": {"custom_resource": 'issue named "Release Ready!"'}}
        with TestClient(app) as client:
            assert client.post("/policies", json=payload).status_code == 401
            assert client.post("/policies", json=payload, headers=headers["developer"]).status_code == 403
            response = client.post("/policies", json=payload, headers=headers["admin"])
            assert response.status_code == 201, response.text
            policy_id = response.json()["id"]
            assert response.json()["conditions"] == {"custom_resource": 'title = "release ready!"', "resource_condition_version": 1}
            metadata_edit = client.put(f"/policies/{policy_id}", headers=headers["admin"], json={"description": "Readable label"})
            assert metadata_edit.status_code == 200 and metadata_edit.json()["conditions"] == response.json()["conditions"]
            duplicate = {**payload, "conditions": {"custom_resource": "Issues called 'RELEASE READY!'"}}
            assert client.post("/policies", json=duplicate, headers=headers["admin"]).status_code == 409

            paths = []
            for path in ("src/Auth.py", "src/auth.py"):
                result = client.post("/policies", headers=headers["admin"], json={
                    **payload, "action": "delete", "resource": "file", "conditions": {"custom_resource": f'path = "{path}"'},
                })
                assert result.status_code == 201, result.text
                assert result.json()["conditions"]["custom_resource"] == f'path = "{path}"'
                paths.append(result.json()["id"])
            assert paths[0] != paths[1]
            branches = []
            for branch in ("Production", "production"):
                result = client.post("/policies", headers=headers["admin"], json={
                    **payload, "resource": "pull_request", "conditions": {"custom_resource": f'target_branch = "{branch}"'},
                })
                assert result.status_code == 201, result.text
                assert result.json()["conditions"]["custom_resource"] == f'target_branch = "{branch}"'
                branches.append(result.json()["id"])
            assert branches[0] != branches[1]
            number = client.post("/policies", headers=headers["admin"], json={
                **payload, "action": "update", "conditions": {"custom_resource": "issue #42"},
            })
            assert number.status_code == 201 and number.json()["conditions"]["custom_resource"] == "number = 42"
            route = 'source_branch != "staging" AND target_branch = "production"'
            branch_payload = {**payload, "resource": "pull_request", "conditions": {
                "custom_resource": 'target_branch = "production" AND source_branch != "staging"',
            }}
            branch = client.post("/policies", headers=headers["admin"], json=branch_payload)
            assert branch.status_code == 201, branch.text
            branch_id = branch.json()["id"]
            assert branch.json()["conditions"] == {"custom_resource": route, "resource_condition_version": 2}
            assert client.post("/policies", headers=headers["admin"], json={
                **branch_payload, "conditions": {"custom_resource": route},
            }).status_code == 409
            assert client.put(f"/policies/{branch_id}", headers=headers["admin"], json={"description": "Branch route"}).status_code == 200
            route_assignment = client.post("/apps/by-client-id/app-1/policy-assignments/resolve", headers=headers["developer"], json={"policy": branch_payload})
            assert route_assignment.status_code == 200 and route_assignment.json()["policy_id"] == branch_id
            global_route = client.post("/global-policy-assignments/resolve", headers=headers["admin"], json={"policy": branch_payload})
            assert global_route.status_code == 200 and global_route.json()["policy_id"] == branch_id
            edited = client.put(f"/apps/by-client-id/app-1/policy-assignments/{route_assignment.json()['assignment_id']}/resolve",
                                headers=headers["developer"], json={"policy": {**branch_payload, "conditions": {
                                    "custom_resource": 'source_branch != "staging" AND target_branch = "release"',
                                }}})
            assert edited.status_code == 200, edited.text
            assert edited.json()["policy_id"] != branch_id
            assert client.get(f"/policies/{branch_id}", headers=headers["admin"]).json()["conditions"]["custom_resource"] == route
            merge_branch = client.post("/policies", headers=headers["admin"], json={**branch_payload, "action": "merge"})
            assert merge_branch.status_code == 201 and merge_branch.json()["conditions"]["resource_condition_version"] == 2
            for title in ("O'Reilly 日本語!", "OReilly 日本語!"):
                result = client.post("/policies", headers=headers["admin"], json={
                    **payload, "conditions": {"custom_resource": f'title = "{title}"'},
                })
                assert result.status_code == 201, result.text
                assert result.json()["conditions"]["custom_resource"] == f'title = "{title.casefold()}"'

            invalid = (
                {"custom_resource": "whose target is production and whose source is not staging"},
                {"custom_resource": "unquoted multiword title"}, {"custom_resource": 42},
                {"custom_resource": "test", "unknown": True},
                {"custom_resource": "test", "resource_condition_version": True},
                {"custom_resource": "test", "resource_condition_version": 2},
                {"custom_resource": "", "resource_condition_version": 1}, {"custom_resource": "x" * 1000},
            )
            for conditions in invalid:
                assert client.post("/policies", headers=headers["admin"], json={**payload, "conditions": conditions}).status_code == 400
            assert client.post("/policies", headers=headers["admin"], json={**payload, "conditions": invalid[0], "enabled": False}).status_code == 400
            assert client.put(f"/policies/{policy_id}", headers=headers["admin"], json={"conditions": invalid[0]}).status_code == 400
            assert client.get(f"/policies/{policy_id}", headers=headers["admin"]).json()["conditions"] == response.json()["conditions"]
            assert client.put(f"/policies/{legacy_ids[0]}", headers=headers["admin"], json={"description": "metadata edit"}).status_code == 400

            draft = {"policy": {**payload, "conditions": {"custom_resource": "legacy"}}, "display_name": "Reviewed App A"}
            endpoint = f"/apps/by-client-id/app-1/policy-assignments/{legacy_assignments[0]}/resolve"
            resolved = client.put(endpoint, headers=headers["developer"], json=draft)
            assert resolved.status_code == 200, resolved.text
            reviewed_id = resolved.json()["policy_id"]
            assert reviewed_id not in legacy_ids
            failed_edit = client.put(endpoint, headers=headers["developer"], json={"policy": {**payload, "conditions": invalid[0]}})
            assert failed_edit.status_code == 400
            assert client.post("/apps/by-client-id/app-2/policy-assignments/resolve", headers=headers["developer"], json=draft).status_code == 403
            rejected = client.post("/global-policy-assignments/resolve", headers=headers["admin"], json={
                "policy": {**payload, "conditions": invalid[0]},
            })
            assert rejected.status_code == 400
            global_result = client.post("/global-policy-assignments/resolve", headers=headers["admin"], json=draft)
            assert global_result.status_code == 200 and global_result.json()["policy_id"] == reviewed_id
            assert client.put(f"/policies/{legacy_ids[0]}", headers=headers["admin"], json={"enabled": False}).status_code == 200
            output = client.post("/policies", headers=headers["admin"], json={
                "policy_type": "output", "category": "custom", "conditions": {"output_rule": "Do not include 'Hello'."},
            })
            assert output.status_code == 201, output.text
            assert output.json()["conditions"] == {"output_rule": "Do not include 'Hello'."}

        with sessions.begin() as db:
            assert db.get(models.AppPolicyAssignmentRecord, legacy_assignments[0]).policy_id == reviewed_id
            assert db.get(models.AppPolicyAssignmentRecord, legacy_assignments[1]).policy_id == legacy_ids[0]
            reviewed = db.get(models.PolicyRecord, reviewed_id)
            duplicate = models.PolicyRecord(**{name: getattr(reviewed, name) for name in (
                "policy_type", "connector", "action", "resource", "connector_id", "action_id", "resource_id",
                "effect", "priority", "conditions", "enabled",
            )})
            db.add(duplicate)
            db.flush()
            duplicate_id = duplicate.id
            db.add(models.AppPolicyAssignmentRecord(app_id=2, policy_id=duplicate_id, display_name="Reviewed shared label"))
            db.flush()
            merges = consolidate_equivalent_policies(db)
            assert duplicate_id in {item.removed_policy_id for item in merges}
            for legacy_id in legacy_ids:
                assert db.get(models.PolicyRecord, legacy_id).conditions == {"custom_resource": "legacy"}
            assert all(db.get(models.PolicyRecord, target_id) is not None for target_id in paths + branches)
            from nemo_mcp_guardrails.database.runtime_policy_snapshot import read_runtime_policy_snapshot
            snapshot = read_runtime_policy_snapshot(db, 1)
            assert any(entry.policy_id == branch_id for entry in snapshot.policies)
            from convert_branch_policies import inventory as branch_inventory, convert
            legacy_routes = [
                ("create", "any non staging branch to production branch"),
                ("merge", "any non staging branch to production branch"),
                ("create", "non development to staging"),
                ("create", "not development branch to staging branch"),
                ("merge", "any source branch to main branch"),
            ]
            converted_ids = []
            for action, selector in legacy_routes:
                row = models.PolicyRecord(policy_type="input", connector="github", action=action, resource="pull_request",
                                          conditions={"custom_resource": selector})
                db.add(row)
                db.flush()
                converted_ids.append(row.id)
            link = models.AppPolicyAssignmentRecord(app_id=2, policy_id=converted_ids[0], display_name="Preserve branch label")
            db.add(link)
            db.flush()
            manifest = branch_inventory(db)
            assert len(manifest.entries) == 5 and not any(entry.approved for entry in manifest.entries)
            approved = manifest.model_copy(update={"entries": [entry.model_copy(update={"approved": True}) for entry in manifest.entries]})
            preview = convert(db, approved)
            assert not preview["applied"] and len(preview["converted_policy_ids"]) == 5
            assert all(db.get(models.PolicyRecord, target_id).policy_version == 1 for target_id in converted_ids)
            bad = approved.model_copy(update={"entries": [approved.entries[0].model_copy(update={"fingerprint": "0" * 64}), *approved.entries[1:]]})
            try:
                convert(db, bad, apply=True)
            except ValueError:
                pass
            else:
                raise AssertionError("Stale conversion manifest was accepted")
            assert all(db.get(models.PolicyRecord, target_id).policy_version == 1 for target_id in converted_ids)
            assert convert(db, approved, apply=True)["converted_policy_ids"] == converted_ids
            assert all(db.get(models.PolicyRecord, target_id).enabled and db.get(models.PolicyRecord, target_id).policy_version == 2 for target_id in converted_ids)
            assert link.policy_id == converted_ids[0] and link.display_name == "Preserve branch label"
            assert not branch_inventory(db).entries
            assignment = db.scalar(select(models.AppPolicyAssignmentRecord).where(
                models.AppPolicyAssignmentRecord.app_id == 2, models.AppPolicyAssignmentRecord.policy_id == reviewed_id,
            ))
            assert assignment.display_name == "Reviewed shared label"
            report = {row["policy_id"]: row for row in inventory(db)["entries"]}
            assert report[reviewed_id]["status"] == "literal_review"
        engine.dispose()
    print("Input condition storage passed: real JWT/RBAC, literal identities, safe edits, legacy isolation and inventory.")


if __name__ == "__main__":
    main()
