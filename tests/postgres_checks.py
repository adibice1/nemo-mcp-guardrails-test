"""Container-only migration/constraint and explicit PostgreSQL diagnostic driver."""

import os
from pathlib import Path
import subprocess
import sys

from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from nemo_mcp_guardrails.database.connection import engine, SessionLocal
from nemo_mcp_guardrails.database.models import Base, PolicyRecord
from migrate_app_main_models import migrate


DIAGNOSTICS = (
    "test_policy_loader", "test_app_policy_scope", "test_app_auth", "test_app_auth_http",
    "test_policy_assignment_api", "test_policy_auto_compile", "test_policy_metadata_api",
    "test_guardrails_run_http", "test_runtime_connector_access", "test_app_connector_api",
    "test_policy_resolution_api", "test_policy_deduplication", "test_management_auth_http",
    "test_management_rbac_http", "test_management_users_http", "test_llm_config_api",
)


def verify_schema() -> None:
    """Exercise additive migration, repeat-run safety, constraints and cascades."""
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE llm_configs DROP CONSTRAINT ck_llm_configs_owned_credential"))
        connection.execute(text("ALTER TABLE llm_configs DROP CONSTRAINT fk_llm_configs_owner_app"))
        connection.execute(text("ALTER TABLE llm_configs DROP COLUMN owner_app_id"))
        connection.execute(text("ALTER TABLE llm_configs DROP COLUMN encrypted_api_key"))
    try:
        with engine.begin() as connection:
            migrate(connection, "wrong-database")
    except ValueError:
        pass
    else:
        raise AssertionError("Migration accepted the wrong database")
    assert "owner_app_id" not in {item["name"] for item in inspect(engine).get_columns("llm_configs")}
    for _ in range(2):
        with engine.begin() as connection:
            migrate(connection, engine.url.database)
    inspector = inspect(engine)
    assert {"owner_app_id", "encrypted_api_key"} <= {item["name"] for item in inspector.get_columns("llm_configs")}
    assert "ix_llm_configs_owner_app_id" in {item["name"] for item in inspector.get_indexes("llm_configs")}
    assert "fk_llm_configs_owner_app" in {item["name"] for item in inspector.get_foreign_keys("llm_configs")}
    assert "ck_llm_configs_owned_credential" in {item["name"] for item in inspector.get_check_constraints("llm_configs")}
    with engine.begin() as connection:
        owner = connection.scalar(text("INSERT INTO apps(name,client_id,api_key_hash,authorized) VALUES ('Fixture','schema-fixture','synthetic',true) RETURNING id"))
    for name, owner_id, ciphertext, reference, expected in (
        ("missing-ciphertext", owner, None, None, "23514"),
        ("mixed-mode", owner, "fixture", "env:FIXTURE", "23514"),
        ("unowned-ciphertext", None, "fixture", None, "23514"),
        ("unknown-owner", 9999999, "fixture", None, "23503"),
    ):
        try:
            with engine.begin() as connection:
                connection.execute(text("INSERT INTO llm_configs(name,provider,model_name,endpoint,credential_reference,owner_app_id,encrypted_api_key,enabled) VALUES (:name,'openai_compatible','fixture','http://127.0.0.1:11434/v1',:reference,:owner,:cipher,true)"),
                                   {"name": name, "reference": reference, "owner": owner_id, "cipher": ciphertext})
        except IntegrityError as error:
            assert error.orig.sqlstate == expected
        else:
            raise AssertionError("Invalid owned credential accepted: " + name)
    with engine.begin() as connection:
        model = connection.scalar(text("INSERT INTO llm_configs(name,provider,model_name,endpoint,owner_app_id,encrypted_api_key,enabled) VALUES ('cascade','openai_compatible','fixture','http://127.0.0.1:11434/v1',:owner,'fixture',true) RETURNING id"), {"owner": owner})
        connection.execute(text("INSERT INTO app_llm_grants(app_id,purpose,llm_config_id,enabled) VALUES (:owner,'main',:model,true)"), {"owner": owner, "model": model})
        connection.execute(text("UPDATE apps SET main_llm_config_id=:model WHERE id=:owner"), {"owner": owner, "model": model})
        connection.execute(text("DELETE FROM apps WHERE id=:owner"), {"owner": owner})
        assert connection.scalar(text("SELECT count(*) FROM llm_configs WHERE id=:model"), {"model": model}) == 0
        assert connection.scalar(text("SELECT count(*) FROM app_llm_grants WHERE llm_config_id=:model"), {"model": model}) == 0
    print("Migration, wrong-target refusal, idempotency, index, constraints and cascade PASS", flush=True)


def run_diagnostic(name: str) -> int:
    """Run one explicit diagnostic in a fresh interpreter with inherited synthetic env."""
    return subprocess.run([sys.executable, "-B", str(Path(__file__).with_name(name + ".py"))],
                          timeout=180).returncode


def run_scope_diagnostic() -> int:
    """Supply only the input/global-output fixtures required by the legacy test."""
    from fastapi.testclient import TestClient
    from _management_auth import install_management_admin_override
    from nemo_mcp_guardrails.api.main import app
    from test_policy_auto_compile import ensure_global_connector, delete_global_connector_if_created

    install_management_admin_override()
    connector_id, created = ensure_global_connector()
    identifiers = []
    try:
        with TestClient(app) as client:
            for body in (
                {"policy_type": "input", "connector": "github", "action": "create", "resource": "issue", "effect": "block", "enabled": True},
                {"policy_type": "output", "category": "scope-fixture", "conditions": {"output_rule": "Do not disclose API keys or credentials."}, "effect": "block", "enabled": True},
            ):
                response = client.post("/policies", json=body)
                assert response.status_code == 201, response.status_code
                identifiers.append(response.json()["id"])
            assert client.post("/global-policy-assignments", json={"policy_ids": [identifiers[1]], "enabled": True}).status_code == 201
        return run_diagnostic("test_app_policy_scope")
    finally:
        with SessionLocal() as db:
            for identifier in identifiers:
                record = db.get(PolicyRecord, identifier)
                if record:
                    db.delete(record)
            db.commit()
        delete_global_connector_if_created(created, connector_id)


def main() -> None:
    """Refuse existing/non-dedicated database targets before any schema operation."""
    if not (os.environ.get("GMS_DISPOSABLE_VERIFICATION") == "1"
            and os.environ.get("PYTHON_DOTENV_DISABLED") == "1"
            and engine.dialect.name == "postgresql" and engine.url.host == "postgres"
            and engine.url.database == "nemo_restore_check_automation"):
        raise SystemExit("Use scripts/run_postgres_checks.py --run; existing databases are not accepted.")
    if inspect(engine).get_table_names():
        raise SystemExit("Disposable database must be empty; refusing existing data.")
    verify_schema()
    from seed_normalized_policy_metadata import main as seed
    seed()
    failures = []
    for name in DIAGNOSTICS:
        print("Checking " + name, flush=True)
        try:
            code = run_scope_diagnostic() if name == "test_app_policy_scope" else run_diagnostic(name)
        except subprocess.TimeoutExpired:
            code = 124
        print(name + (" PASS" if code == 0 else " FAIL"), flush=True)
        if code:
            failures.append(name)
    print(f"PostgreSQL diagnostics: {len(DIAGNOSTICS) - len(failures)} passed, {len(failures)} failed.", flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
