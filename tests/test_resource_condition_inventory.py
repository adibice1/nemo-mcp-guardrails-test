"""Disposable SQLite checks for a non-mutating, metadata-only policy inventory."""

import io
import json
import os
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from unittest.mock import patch

from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import JSON, MetaData, create_engine, event, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import inventory_resource_conditions as module
from nemo_mcp_guardrails.database import models


def main() -> None:
    """Verify compatibility flags, normalized metadata, scope and safe CLI opt-in."""

    with patch.object(module, "create_engine") as connect, patch("dotenv.load_dotenv") as dotenv:
        with redirect_stdout(io.StringIO()):
            module.main([])
        connect.assert_not_called()
        dotenv.assert_not_called()

    with ExitStack() as cleanup:
        url = "sqlite://"
        engine = create_engine(url, poolclass=StaticPool)
        cleanup.callback(engine.dispose)
        metadata = MetaData()
        for table in models.Base.metadata.sorted_tables:
            cloned = table.to_metadata(metadata)
            for column in cloned.columns:
                if isinstance(column.type, JSONB):
                    column.type = JSON()
                    column.server_default = None
        metadata.create_all(engine)
        with engine.begin() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys = ON")
        with Session(engine) as db, db.begin():
            connector = models.ConnectorRecord(name="github", display_name="GitHub")
            db.add(connector)
            db.flush()
            action = models.ConnectorActionRecord(connector_id=connector.id, name="create", display_name="Create")
            resource = models.ConnectorResourceRecord(connector_id=connector.id, name="issue", display_name="Issue")
            db.add_all([action, resource])
            db.flush()
            definitions = [
                models.PolicyRecord(policy_type="input", connector="github", action="create", resource="issue", conditions={}),
                models.PolicyRecord(policy_type="input", connector="stale", action="stale", resource="stale",
                                    connector_id=connector.id, action_id=action.id, resource_id=resource.id,
                                    conditions={"custom_resource": 'title = "PRIVATE_LITERAL_MARKER"'}),
                models.PolicyRecord(policy_type="input", connector="github", action="merge", resource="pull_request",
                                    conditions={"custom_resource": 'target_branch = "production"'}),
                models.PolicyRecord(policy_type="input", connector="github", action="create", resource="issue",
                                    conditions={"custom_resource": "legacy multiword title"}, enabled=False),
                models.PolicyRecord(policy_type="input", connector="github", action="create", resource="issue",
                                    conditions={"custom_resource": "test", "unknown_condition": True}),
                models.PolicyRecord(policy_type="input", connector="github", action="create", resource="issue", conditions=["bad"]),
                models.PolicyRecord(policy_type="output", category="custom", conditions={"output_rule": "private"}),
            ]
            app = models.AppRecord(client_id="inventory-app", name="Inventory App", api_key_hash="unused")
            db.add_all([*definitions, app])
            db.flush()
            ids = [item.id for item in definitions]
            app_id = app.id
            db.add_all([
                models.GlobalPolicyAssignmentRecord(policy_id=ids[0]),
                models.AppPolicyAssignmentRecord(policy_id=ids[1], app_id=app.id),
                models.AppPolicyAssignmentRecord(policy_id=ids[2], app_id=app.id, enabled=False),
            ])
        statements = []

        def record_statement(connection, cursor, statement, parameters, context, executemany):
            """Record SQL verbs after fixture setup without logging parameter values."""

            statements.append(statement.lstrip().split()[0].upper())

        event.listen(engine, "before_cursor_execute", record_statement)
        with Session(engine) as db:
            dirty = db.get(models.PolicyRecord, ids[0])
            dirty.description = "Uncommitted change must not autoflush."
            result = module.inventory(db)
            assert dirty in db.dirty
        entries = {row["policy_id"]: row for row in result["entries"]}
        assert len(entries) == 6 and ids[-1] not in entries
        assert entries[ids[0]]["status"] == "broad" and entries[ids[0]]["global_assignment_enabled"]
        assert entries[ids[1]]["status"] == "literal_review"
        assert entries[ids[1]]["enabled_app_ids"] == [app_id]
        assert entries[ids[1]]["field"] == "title" and entries[ids[1]]["requires_admin_review"]
        assert entries[ids[2]]["enabled_app_ids"] == []
        assert entries[ids[2]]["status"] == "literal_review"
        assert entries[ids[2]]["field"] == "target_branch"
        assert all(entries[item]["status"] == "unsupported" for item in ids[3:6])
        assert entries[ids[3]]["enabled"] is False
        assert "PRIVATE_LITERAL_MARKER" not in json.dumps(result)
        assert set(statements) == {"SELECT"}

        output = io.StringIO()
        with patch.dict(os.environ, {"DATABASE_URL": url}), patch("dotenv.load_dotenv") as dotenv, \
             patch.object(module, "create_engine", return_value=engine), patch.object(engine, "dispose"):
            with redirect_stdout(output):
                module.main(["--database"])
            dotenv.assert_called_once()
        assert json.loads(output.getvalue()) == result

        def attempt_write(db):
            """Prove the CLI connection refuses a write even if its reader regresses."""

            db.execute(models.PolicyRecord.__table__.update().values(description="PRIVATE_WRITE_MARKER"))

        error_output = io.StringIO()
        with patch.dict(os.environ, {"DATABASE_URL": url}), patch("dotenv.load_dotenv"), \
             patch.object(module, "create_engine", return_value=engine), patch.object(engine, "dispose"), \
             patch.object(module, "inventory", side_effect=attempt_write), redirect_stderr(error_output):
            try:
                module.main(["--database"])
            except SystemExit as error:
                assert error.code == 2
            else:
                raise AssertionError("Inventory CLI allowed a database write.")
        assert "PRIVATE_WRITE_MARKER" not in error_output.getvalue()
        with Session(engine) as db:
            assert db.scalar(select(models.PolicyRecord.description).where(models.PolicyRecord.id == ids[0])) is None
    print("Resource inventory passed: read-only scope, review flags, private-value omission and explicit opt-in.")


if __name__ == "__main__":
    main()
