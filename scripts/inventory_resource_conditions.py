"""Report stored input-condition compatibility without rewriting policies."""

import argparse
import json
import os

from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.database.models import (
    AppPolicyAssignmentRecord, ConnectorActionRecord, ConnectorRecord,
    ConnectorResourceRecord, GlobalPolicyAssignmentRecord, PolicyRecord,
)
from nemo_mcp_guardrails.github_resource_bindings import compile_resource_binding
from nemo_mcp_guardrails.input_conditions import CONDITION_VERSION_KEY, prepare_input_conditions
from nemo_mcp_guardrails.policy_compiler import InputPolicyObject
from nemo_mcp_guardrails.resource_conditions import UnsupportedResourceCondition
from nemo_mcp_guardrails.resource_conditions import condition_terms


def inventory(db: Session) -> dict:
    """Select input definitions and enabled assignment scope without autoflush."""

    with db.no_autoflush:
        globals_enabled = set(db.scalars(select(GlobalPolicyAssignmentRecord.policy_id).where(
            GlobalPolicyAssignmentRecord.enabled.is_(True),
        )))
        app_links: dict[int, list[int]] = {}
        for policy_id, app_id in db.execute(select(
            AppPolicyAssignmentRecord.policy_id, AppPolicyAssignmentRecord.app_id,
        ).where(AppPolicyAssignmentRecord.enabled.is_(True)).order_by(AppPolicyAssignmentRecord.app_id)):
            app_links.setdefault(policy_id, []).append(app_id)
        rows = db.execute(select(
            PolicyRecord.id, PolicyRecord.enabled, PolicyRecord.effect, PolicyRecord.conditions,
            func.coalesce(ConnectorRecord.name, PolicyRecord.connector).label("connector"),
            func.coalesce(ConnectorActionRecord.name, PolicyRecord.action).label("action"),
            func.coalesce(ConnectorResourceRecord.name, PolicyRecord.resource).label("resource"),
        ).outerjoin(ConnectorRecord, PolicyRecord.connector_id == ConnectorRecord.id)
         .outerjoin(ConnectorActionRecord, PolicyRecord.action_id == ConnectorActionRecord.id)
         .outerjoin(ConnectorResourceRecord, PolicyRecord.resource_id == ConnectorResourceRecord.id)
         .where(PolicyRecord.policy_type == "input").order_by(PolicyRecord.id))
        entries = []
        for row in rows:
            binding = None
            try:
                conditions = row.conditions if row.conditions is not None else {}
                if not isinstance(conditions, dict) or set(conditions) - {"custom_resource", CONDITION_VERSION_KEY}:
                    raise UnsupportedResourceCondition("Unsupported input condition fields.")
                policy = InputPolicyObject(
                    connector=row.connector, action=row.action, resource=row.resource,
                    effect=row.effect, custom_resource=conditions.get("custom_resource"),
                )
                if CONDITION_VERSION_KEY in conditions and prepare_input_conditions(policy, conditions) != conditions:
                    raise UnsupportedResourceCondition("Stored selector requires review.")
                binding = compile_resource_binding(policy)
                status = "literal_review" if binding else "broad"
            except UnsupportedResourceCondition:
                status = "unsupported"
            entries.append({
                "policy_id": row.id, "enabled": row.enabled,
                "global_assignment_enabled": row.id in globals_enabled,
                "enabled_app_ids": app_links.get(row.id, []),
                "status": status, "field": ",".join(term.field for term in condition_terms(binding.condition)) if binding else None,
                "requires_admin_review": status != "broad",
            })
    return {"format": "resource-condition-inventory-v1", "entries": entries}


def main(argv: list[str] | None = None) -> None:
    """Require explicit database opt-in and enforce a read-only transaction."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", action="store_true", help="Read the configured database; never apply changes.")
    args = parser.parse_args(argv)
    if not args.database:
        parser.print_help()
        return
    engine = None
    try:
        from dotenv import load_dotenv

        load_dotenv()
        url = os.getenv("DATABASE_URL")
        if not url:
            raise ValueError("DATABASE_URL is required.")
        engine = create_engine(url)
        if engine.dialect.name not in {"postgresql", "sqlite"}:
            raise ValueError("Unsupported inventory database dialect.")
        if engine.dialect.name == "sqlite" and engine.url.database not in {None, "", ":memory:"}:
            raise ValueError("SQLite CLI inventory is limited to disposable in-memory diagnostics.")
        with engine.connect() as connection:
            if engine.dialect.name == "sqlite":
                connection.exec_driver_sql("PRAGMA query_only = ON")
            else:
                connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
            with Session(bind=connection, autoflush=False) as db:
                result = inventory(db)
            connection.rollback()
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, SQLAlchemyError):
        parser.exit(2, "Inventory stopped: invalid policy or database state; private values are omitted.\n")
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    main()
