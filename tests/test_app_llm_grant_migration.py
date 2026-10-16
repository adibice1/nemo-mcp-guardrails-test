"""Offline schema, inventory and explicit grant-seeding regressions."""

import copy
import io
import json
import os
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import create_engine, delete, event, func, inspect, select, update
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateIndex, CreateTable

from migrate_app_llm_grants import GrantManifest, inventory, main as migrate, seed_manifest
from nemo_mcp_guardrails.database.models import AppLlmGrantRecord, AppRecord, LlmConfigRecord


def main() -> None:
    """Use only disposable SQLite and fake metadata; PostgreSQL DDL is compile-only."""

    check = TestCase()
    settings = {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "AZURE_OPENAI_ENDPOINT": "https://fake.openai.azure.com",
        "AZURE_OPENAI_DEPLOYMENT": "fake-default", "AZURE_OPENAI_API_VERSION": "fake-version",
    }
    with patch.dict(os.environ, settings):
        from nemo_mcp_guardrails.database import connection

        engine = create_engine("sqlite://")

        @event.listens_for(engine, "connect")
        def enforce_foreign_keys(dbapi_connection, _):
            """Exercise actual SQLite foreign-key constraints and cascades."""
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

        for record in (LlmConfigRecord, AppRecord):
            record.__table__.create(engine)
        with Session(engine) as db, db.begin():
            db.add(LlmConfigRecord(
                id=1, name="Fake named model", provider="azure_openai", model_name="fake-model",
                endpoint="https://fake.openai.azure.com", credential_reference="env:PRIVATE_MARKER",
                enabled=True,
            ))
            db.flush()
            db.add_all([
                AppRecord(id=1, name="App A", client_id="a", api_key_hash="unused", authorized=True,
                          main_llm_config_id=1),
                AppRecord(id=2, name="App B", client_id="b", api_key_hash="unused", authorized=False),
            ])

        statements = []

        @event.listens_for(engine, "before_cursor_execute")
        def capture_sql(_, __, statement, ___, ____, _____):
            """Observe that preview operations do not issue schema or data writes."""
            statements.append(statement.lstrip().split()[0].upper())

        with patch.object(connection, "engine", engine):
            output, errors = io.StringIO(), io.StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                migrate([])
            raw = json.loads(output.getvalue())
            assert len(raw["entries"]) == 4 and not any(row["enabled"] for row in raw["entries"])
            assert "PRIVATE_MARKER" not in output.getvalue() + errors.getvalue()
            assert "CREATE TABLE app_llm_grants" in errors.getvalue()
            assert not inspect(engine).has_table("app_llm_grants")
            assert not set(statements) & {"CREATE", "INSERT", "UPDATE", "DELETE", "ALTER", "DROP"}
            with Session(engine) as db:
                assert seed_manifest(db, GrantManifest.model_validate(raw))["new_grants"] == 0
                with check.assertRaises(ValueError):
                    seed_manifest(db, GrantManifest.model_validate(raw), apply=True)
                with patch("migrate_app_llm_grants.os.getenv", wraps=os.getenv) as lookup:
                    inventory(db)
                assert {call.args[0] for call in lookup.call_args_list} == {
                    "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT", "AZURE_OPENAI_API_VERSION",
                }
            for _ in range(2):
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    migrate(["--apply-schema"])
            assert set(inspect(engine).get_table_names()) == {"apps", "llm_configs", "app_llm_grants"}

            reviewed = copy.deepcopy(raw)
            reviewed["entries"][0]["enabled"] = True
            reviewed["entries"][1]["enabled"] = True
            manifest = GrantManifest.model_validate(reviewed)
            statements.clear()
            with Session(engine) as db:
                assert seed_manifest(db, manifest)["new_grants"] == 2
                assert db.scalar(select(func.count()).select_from(AppLlmGrantRecord)) == 0
            assert not set(statements) & {"CREATE", "INSERT", "UPDATE", "DELETE", "ALTER", "DROP"}
            for invalid in (
                dict(reviewed, unexpected=True),
                dict(reviewed, entries=[dict(reviewed["entries"][0], enabled="true")]),
                dict(reviewed, entries=[dict(reviewed["entries"][0], app_id=True)]),
            ):
                with check.assertRaises(ValueError):
                    GrantManifest.model_validate(invalid)
            for changed in (
                {"client_id": "renamed"}, {"llm_config_id": 1},
                {"fingerprint": "0" * 64}, {"app_id": 999}, {"config_name": "changed"},
            ):
                invalid = copy.deepcopy(reviewed)
                invalid["entries"][-1].update(changed)
                with Session(engine) as db, db.begin(), check.assertRaises(ValueError):
                    seed_manifest(db, GrantManifest.model_validate(invalid), apply=True)
            duplicate = copy.deepcopy(reviewed)
            duplicate["entries"].append(duplicate["entries"][0])
            with Session(engine) as db, db.begin(), check.assertRaises(ValueError):
                seed_manifest(db, GrantManifest.model_validate(duplicate), apply=True)

            for values in (
                {"credential_reference": "env:CHANGED"}, {"endpoint": "https://changed.invalid"},
                {"enabled": False}, {"model_name": "changed"},
            ):
                with Session(engine) as db, db.begin():
                    db.execute(update(LlmConfigRecord).where(LlmConfigRecord.id == 1).values(**values))
                    with check.assertRaises(ValueError):
                        seed_manifest(db, manifest, apply=True)
                    db.rollback()
            for values in (
                {"name": "changed"}, {"client_id": "changed"}, {"authorized": False},
                {"main_llm_config_id": None},
            ):
                with Session(engine) as db, db.begin():
                    db.execute(update(AppRecord).where(AppRecord.id == 1).values(**values))
                    with check.assertRaises(ValueError):
                        seed_manifest(db, manifest, apply=True)
                    db.rollback()
            with Session(engine) as db, db.begin():
                db.execute(update(LlmConfigRecord).where(LlmConfigRecord.id == 1).values(enabled=False))
                disabled = inventory(db).model_dump()
                disabled["entries"][0]["enabled"] = True
                with check.assertRaises(ValueError):
                    seed_manifest(db, GrantManifest.model_validate(disabled), apply=True)
                db.rollback()
            with patch.dict(os.environ, {"AZURE_OPENAI_DEPLOYMENT": "changed"}):
                with Session(engine) as db, check.assertRaises(ValueError):
                    seed_manifest(db, manifest, apply=True)
            with Session(engine) as db:
                assert db.scalar(select(func.count()).select_from(AppLlmGrantRecord)) == 0

            def fail_after_insert(_, __, statement, ___, ____, _____):
                """Prove transaction rollback even after an actual grant insert."""
                if statement.startswith("INSERT INTO app_llm_grants"):
                    raise IntegrityError("synthetic insert failure", {}, RuntimeError())

            event.listen(engine, "after_cursor_execute", fail_after_insert)
            try:
                with check.assertRaises(IntegrityError), Session(engine) as db, db.begin():
                    seed_manifest(db, manifest, apply=True)
            finally:
                event.remove(engine, "after_cursor_execute", fail_after_insert)
            with Session(engine) as db:
                assert db.scalar(select(func.count()).select_from(AppLlmGrantRecord)) == 0
            with patch.object(Path, "read_text", return_value=manifest.model_dump_json()):
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    migrate(["--manifest", "reviewed.json"])
                with Session(engine) as db:
                    assert db.scalar(select(func.count()).select_from(AppLlmGrantRecord)) == 0
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    migrate(["--manifest", "reviewed.json", "--apply-manifest"])
            with Session(engine) as db, db.begin():
                assert seed_manifest(db, manifest, apply=True)["new_grants"] == 0
                assert db.scalar(select(func.count()).select_from(AppLlmGrantRecord)) == 2
                app = db.get(AppRecord, 1)
                assert (app.client_id, app.authorized, app.main_llm_config_id,
                        app.guardrail_llm_config_id) == ("a", True, 1, None)
                db.execute(update(AppLlmGrantRecord).where(
                    AppLlmGrantRecord.purpose == "main",
                ).values(enabled=False))
            with Session(engine) as db, db.begin(), check.assertRaises(ValueError):
                seed_manifest(db, manifest, apply=True)
            with Session(engine) as db:
                assert db.scalar(select(AppLlmGrantRecord.enabled).where(
                    AppLlmGrantRecord.purpose == "main",
                )) is False
            with patch.object(Path, "read_text", return_value="PRIVATE_MARKER"):
                errors = io.StringIO()
                with redirect_stderr(errors), check.assertRaises(SystemExit):
                    migrate(["--manifest", "invalid.json", "--apply-manifest"])
                assert "PRIVATE_MARKER" not in errors.getvalue()

        with Session(engine) as db, db.begin():
            db.add_all([
                AppLlmGrantRecord(app_id=1, purpose="main"),
                AppLlmGrantRecord(app_id=1, purpose="guardrail", llm_config_id=1),
                AppLlmGrantRecord(app_id=2, purpose="main", llm_config_id=1),
            ])
            db.flush()
            assert db.scalar(select(func.count()).select_from(AppLlmGrantRecord)) == 5
            assert db.scalar(select(func.count()).select_from(AppLlmGrantRecord).where(
                AppLlmGrantRecord.enabled.is_(False),
            )) == 4
            db.rollback()

        for values in (
            {"app_id": 1, "purpose": "main", "llm_config_id": 1},
            {"app_id": 1, "purpose": "guardrail", "llm_config_id": None},
            {"app_id": 1, "purpose": "invalid"}, {"app_id": 999, "purpose": "main"},
            {"app_id": 1, "purpose": "main", "llm_config_id": 999},
        ):
            with check.assertRaises(IntegrityError), engine.begin() as db:
                db.execute(AppLlmGrantRecord.__table__.insert().values(**values))
        with engine.begin() as db:
            db.execute(AppLlmGrantRecord.__table__.insert().values(app_id=2, purpose="main"))
        with Session(engine) as db:
            grant = db.scalar(select(AppLlmGrantRecord).where(AppLlmGrantRecord.app_id == 2))
            assert grant.enabled is False and grant.created_at and grant.updated_at
        with engine.begin() as db:
            db.execute(delete(LlmConfigRecord).where(LlmConfigRecord.id == 1))
        with Session(engine) as db:
            assert db.scalar(select(func.count()).select_from(AppLlmGrantRecord)) == 2
            assert db.get(AppRecord, 1).main_llm_config_id is None
        with engine.begin() as db:
            db.execute(delete(AppRecord).where(AppRecord.id == 1))
        with Session(engine) as db:
            assert db.scalar(select(func.count()).select_from(AppLlmGrantRecord)) == 1
        ddl = str(CreateTable(AppLlmGrantRecord.__table__).compile(dialect=postgresql.dialect()))
        indexes = "\n".join(str(CreateIndex(index).compile(dialect=postgresql.dialect()))
                            for index in AppLlmGrantRecord.__table__.indexes)
        assert "CHECK (purpose IN ('main', 'guardrail'))" in ddl
        assert "DEFAULT false NOT NULL" in ddl and ddl.count("ON DELETE CASCADE") == 2
        assert "WHERE llm_config_id IS NULL" in indexes
        assert "WHERE llm_config_id IS NOT NULL" in indexes
        engine.dispose()
    print("Grant migration checks passed: SQLite constraints, previews, stale manifests, atomic seeding, and revocation preservation. PostgreSQL DDL compiled only.")


if __name__ == "__main__":
    main()
