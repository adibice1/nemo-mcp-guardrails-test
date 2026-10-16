"""Offline proof of scoped, immutable, single-statement policy snapshots."""

from dataclasses import FrozenInstanceError
from unittest.mock import patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Use in-memory SQLite only; never load environment or construct a runtime."""

    with patch("dotenv.load_dotenv", side_effect=AssertionError("Unexpected dotenv load")):
        from sqlalchemy import JSON, MetaData, create_engine, event, select, update
        from sqlalchemy.dialects import postgresql
        from sqlalchemy.dialects.postgresql import JSONB
        from sqlalchemy.exc import SQLAlchemyError
        from sqlalchemy.orm import sessionmaker
        from nemo_mcp_guardrails.database import models
        from nemo_mcp_guardrails.database import runtime_policy_snapshot as module
        from nemo_mcp_guardrails.database.policy_errors import PolicyLoadError
        from nemo_mcp_guardrails.policy_compiler import (
            InputPolicyObject, OutputPolicyObject, compile_output_rail_rules, compile_policy,
        )

        engine = create_engine("sqlite://")
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
            for app_id in range(1, 5):
                db.add(models.AppRecord(id=app_id, name=f"App {app_id}", client_id=f"app-{app_id}",
                                        api_key_hash="unused", authorized=app_id != 4))
            github = models.ConnectorRecord(name="github", display_name="GitHub")
            other = models.ConnectorRecord(name="other", display_name="Other")
            db.add_all([github, other])
            db.flush()
            action = models.ConnectorActionRecord(connector_id=github.id, name="delete", display_name="Delete")
            resource = models.ConnectorResourceRecord(connector_id=github.id, name="file", display_name="File")
            db.add_all([action, resource])
            db.flush()
            broad = models.PolicyRecord(policy_type="input", connector="github", action="create",
                                        resource="issue", conditions={})
            literal = models.PolicyRecord(policy_type="input", connector="stale-flat", action="stale-flat",
                resource="stale-flat", connector_id=github.id, action_id=action.id, resource_id=resource.id,
                conditions={"custom_resource": 'path = "src/Auth.py"', "resource_condition_version": 1})
            output = models.PolicyRecord(policy_type="output", category="custom", description="Old description",
                                         conditions={"output_rule": "PRIVATE_OUTPUT_MARKER"})
            db.add_all([broad, literal, output])
            db.flush()
            broad_id, literal_id, output_id = broad.id, literal.id, output.id
            connector_id, action_id, resource_id, other_id = github.id, action.id, resource.id, other.id
            texts = {
                broad_id: compile_policy(InputPolicyObject("github", "create", "issue", "block")).input_rail_rule,
                literal_id: compile_policy(InputPolicyObject("github", "delete", "file", "block",
                                                              'path = "src/Auth.py"')).input_rail_rule,
                output_id: compile_output_rail_rules((OutputPolicyObject("custom", "PRIVATE_OUTPUT_MARKER", "block"),))[0],
            }
            for policy in (broad, literal, output):
                db.add(models.CompiledPolicyRuleRecord(policy_id=policy.id, rail_type=policy.policy_type,
                                                       rule_text=texts[policy.id]))
            db.add_all([
                models.GlobalPolicyAssignmentRecord(policy_id=broad_id),
                models.GlobalPolicyAssignmentRecord(policy_id=output_id),
                models.AppPolicyAssignmentRecord(app_id=1, policy_id=literal_id),
                models.AppPolicyAssignmentRecord(app_id=1, policy_id=broad_id),
                models.CompiledPolicyRuleRecord(policy_id=literal_id, rail_type="input", enabled=False,
                                                stale=True, rule_text="DISABLED_HISTORY"),
            ])
            # Malformed out-of-scope definitions must not break App 1.
            for index in range(5):
                record = models.PolicyRecord(policy_type="input", connector="github", action="merge",
                    resource="pull_request", conditions={"custom_resource": "unsupported compound"}, enabled=index != 3)
                db.add(record)
                db.flush()
                if index == 0:
                    db.add(models.AppPolicyAssignmentRecord(app_id=2, policy_id=record.id))
                elif index == 1:
                    db.add(models.AppPolicyAssignmentRecord(app_id=1, policy_id=record.id, enabled=False))
                elif index == 2:
                    db.add(models.GlobalPolicyAssignmentRecord(policy_id=record.id, enabled=False))
                elif index == 3:
                    db.add(models.AppPolicyAssignmentRecord(app_id=1, policy_id=record.id))
            db.flush()

        def unavailable(db, app_id=1) -> None:
            """Require one controlled error without literal or database details."""

            try:
                module.read_runtime_policy_snapshot(db, app_id)
            except PolicyLoadError as error:
                assert str(error) == "Runtime policy snapshot is unavailable."
                assert error.__suppress_context__
            else:
                raise AssertionError("Invalid selected state was accepted")

        statements = []

        def capture(connection, cursor, statement, parameters, context, executemany) -> None:
            """Count SQL emitted by the reader, excluding fixture writes."""

            statements.append(statement)

        with sessions() as db:
            cached_policy = db.get(models.PolicyRecord, literal_id)
            cached_policy.conditions = {"custom_resource": "PRIVATE_DIRTY_MARKER"}
            db.add(models.PolicyRecord(policy_type="input", connector="PRIVATE_PENDING_MARKER"))
            event.listen(engine, "before_cursor_execute", capture)
            try:
                first = module.read_runtime_policy_snapshot(db, 1)
            finally:
                event.remove(engine, "before_cursor_execute", capture)
            assert len(statements) == 1 and statements[0].lstrip().upper().startswith("SELECT")
            assert len(db.new) == 1  # Even an autoflush-enabled caller cannot flush here.
            assert len(db.dirty) == 1 and cached_policy.conditions == {"custom_resource": "PRIVATE_DIRTY_MARKER"}
            assert {entry.policy_id for entry in first.policies} == {broad_id, literal_id, output_id}
            target = next(entry for entry in first.policies if entry.policy_id == literal_id)
            assert target.policy == InputPolicyObject("github", "delete", "file", "block", 'path = "src/Auth.py"')
            assert "Auth.py" not in repr(first) and "PRIVATE_OUTPUT_MARKER" not in repr(first)
            hash(first)
            try:
                target.policy.custom_resource = "replacement"
            except FrozenInstanceError:
                pass
            else:
                raise AssertionError("Policy snapshot was mutable")
            assert module.read_runtime_policy_snapshot(db, 1) == first
            assert {entry.policy_id for entry in module.read_runtime_policy_snapshot(db, 3).policies} == {broad_id, output_id}
            unavailable(db, 2)
            unavailable(db, 4)
            unavailable(db, 999)

        # Invalid IDs fail before any database access.
        for invalid_id in (None, True, 0, -1, "1"):
            with patch.object(module, "_snapshot_statement", side_effect=AssertionError("Unexpected query")):
                try:
                    module.read_runtime_policy_snapshot(None, invalid_id)
                except PolicyLoadError:
                    pass
                else:
                    raise AssertionError("Invalid app ID was accepted")

        policy_table = models.PolicyRecord.__table__
        rule_table = models.CompiledPolicyRuleRecord.__table__
        malformed_conditions = (
            [], {"unknown": "PRIVATE_CONDITION_MARKER"}, {"custom_resource": 42},
            {"custom_resource": "src/Auth.py"},  # Legacy selectors need explicit review.
            {"custom_resource": 'path = "src/Auth.py"'},
            {"custom_resource": 'path = "src/Auth.py"', "resource_condition_version": True},
            {"custom_resource": 'path = "src/Auth.py"', "resource_condition_version": 2},
            {"custom_resource": "", "resource_condition_version": 1},
            {"custom_resource": 'path="src/Auth.py"', "resource_condition_version": 1},
            {"custom_resource": 'path = "src/Auth.py" AND title = "x"', "resource_condition_version": 1},
        )
        for conditions in malformed_conditions:
            with sessions() as db:
                db.execute(update(policy_table).where(policy_table.c.id == literal_id).values(conditions=conditions))
                unavailable(db)
        for values in ({"effect": "allow"}, {"policy_type": "unknown"}, {"policy_version": 0},
                       {"connector_id": 9999}, {"action_id": 9999}, {"resource_id": 9999},
                       {"action_id": None, "action": "read"}, {"resource_id": None, "resource": "branch"}):
            with sessions() as db:
                db.execute(update(policy_table).where(policy_table.c.id == literal_id).values(**values))
                unavailable(db)
        for values in ({"action": "read", "resource": "file"}, {"connector": "sharepoint"},
                       {"conditions": {"unknown": "PRIVATE_CONDITION_MARKER"}}):
            with sessions() as db:
                db.execute(update(policy_table).where(policy_table.c.id == broad_id).values(**values))
                unavailable(db)
        for table, identifier, values in (
            (models.ConnectorRecord.__table__, connector_id, {"enabled": False}),
            (models.ConnectorActionRecord.__table__, action_id, {"enabled": False}),
            (models.ConnectorResourceRecord.__table__, resource_id, {"enabled": False}),
            (models.ConnectorActionRecord.__table__, action_id, {"connector_id": other_id}),
            (models.ConnectorResourceRecord.__table__, resource_id, {"connector_id": other_id}),
        ):
            with sessions() as db:
                db.execute(update(table).where(table.c.id == identifier).values(**values))
                unavailable(db)
        for values in ({"enabled": False}, {"stale": True}, {"rail_type": "output"},
                       {"policy_version": 99}, {"rule_text": "PRIVATE_STALE_MARKER"}):
            with sessions() as db:
                db.execute(update(rule_table).where(rule_table.c.policy_id == literal_id,
                    rule_table.c.enabled.is_(True)).values(**values))
                unavailable(db)
        with sessions() as db:
            db.add(models.CompiledPolicyRuleRecord(policy_id=literal_id, rail_type="input", rule_text=texts[literal_id]))
            db.flush()
            unavailable(db)
        with sessions() as db:
            db.execute(update(rule_table).where(rule_table.c.policy_id == literal_id,
                rule_table.c.enabled.is_(False)).values(enabled=True))
            unavailable(db)  # Enabled stale history is not silently ignored.
        for values in ({"conditions": []}, {"category": ""}, {"conditions": {"output_rule": 123}},
                       {"conditions": {"output_rule": ""}}):
            with sessions() as db:
                db.execute(update(policy_table).where(policy_table.c.id == output_id).values(**values))
                unavailable(db)
        with sessions() as db:
            # Older broad/description-backed policies need no invented format marker.
            db.execute(update(policy_table).where(policy_table.c.id == broad_id).values(conditions=None))
            db.execute(update(policy_table).where(policy_table.c.id == output_id).values(conditions={}))
            legacy_text, = compile_output_rail_rules((OutputPolicyObject("custom", "Old description", "block"),))
            db.execute(update(rule_table).where(rule_table.c.policy_id == output_id).values(rule_text=legacy_text))
            compatible = module.read_runtime_policy_snapshot(db, 1)
            assert next(entry for entry in compatible.policies if entry.policy_id == broad_id).policy.custom_resource is None
            assert next(entry for entry in compatible.policies if entry.policy_id == output_id).policy.description == "Old description"

        # Exact content changes must be detectable even when count/version/timestamps stay equal.
        with sessions() as db:
            before = module.read_runtime_policy_snapshot(db, 1)
            timestamps = db.execute(select(policy_table.c.updated_at, rule_table.c.updated_at)
                .join(rule_table, rule_table.c.policy_id == policy_table.c.id)
                .where(policy_table.c.id == literal_id, rule_table.c.enabled.is_(True))).one()
            selector = 'path = "src/auth.py"'
            new_text = compile_policy(InputPolicyObject("github", "delete", "file", "block", selector)).input_rail_rule
            db.execute(update(policy_table).where(policy_table.c.id == literal_id).values(
                conditions={"custom_resource": selector, "resource_condition_version": 1}, updated_at=timestamps[0]))
            unavailable(db)  # Old compiled text is not an acceptable fallback.
            db.execute(update(rule_table).where(rule_table.c.policy_id == literal_id,
                rule_table.c.enabled.is_(True)).values(rule_text=new_text, updated_at=timestamps[1]))
            after = module.read_runtime_policy_snapshot(db, 1)
            assert before != after and len(before.policies) == len(after.policies)
            assert target.policy.custom_resource == 'path = "src/Auth.py"'
        with sessions() as db:
            db.execute(update(models.GlobalPolicyAssignmentRecord).values(enabled=False))
            assert module.read_runtime_policy_snapshot(db, 3).policies == ()
            # Enabled global policy failures affect every app, even without app assignments.
            db.rollback()
            db.execute(update(policy_table).where(policy_table.c.id == broad_id).values(effect="allow"))
            unavailable(db, 1)
            unavailable(db, 3)
        with sessions() as db, patch.object(db, "execute", side_effect=SQLAlchemyError("PRIVATE_DB_MARKER")):
            unavailable(db)
        sql = str(module._snapshot_statement(1).compile(dialect=postgresql.dialect()))
        assert sql.lstrip().startswith("SELECT") and "EXISTS" in sql and "LEFT OUTER JOIN" in sql
        engine.dispose()
        print("Runtime snapshot passed: one SELECT, exact contents, scope, immutable values and fail-closed validation.")


if __name__ == "__main__":
    main()
