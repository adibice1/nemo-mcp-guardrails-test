"""Rehearse the recorded legacy issue-title repair using synthetic SQLite only."""

from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import JSON, MetaData, create_engine, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.database import models
from nemo_mcp_guardrails.github_resource_bindings import compile_resource_binding
from nemo_mcp_guardrails.input_conditions import prepare_input_conditions
from nemo_mcp_guardrails.policy_compiler import InputPolicyObject
from nemo_mcp_guardrails.policy_rule_service import refresh_compiled_policy_rule
from nemo_mcp_guardrails.resource_conditions import UnsupportedResourceCondition


LEGACY = "any issue where the title or name is exactly test"


def main() -> None:
    """Verify a reviewed canonical candidate without connecting to policy 210."""
    policy = InputPolicyObject("github", "create", "issue", "block", LEGACY)
    try:
        prepare_input_conditions(policy, {"custom_resource": LEGACY})
    except UnsupportedResourceCondition:
        pass
    else:
        raise AssertionError("Legacy prose unexpectedly accepted")
    proposed = prepare_input_conditions(policy, {"custom_resource": 'title = "test"'})
    assert proposed == {"custom_resource": 'title = "test"', "resource_condition_version": 1}
    binding = compile_resource_binding(InputPolicyObject("github", "create", "issue", "block",
                                                        proposed["custom_resource"]))
    assert binding is not None
    for title in ("test", "TEST"):
        assert binding.matches("issue_write", {"method": "create", "title": title})
    for title in ("contest", "testing", "other"):
        assert not binding.matches("issue_write", {"method": "create", "title": title})
    assert not binding.matches("issue_write", {"method": "update", "title": "test"})
    assert not binding.matches("list_issues", {"title": "test"})

    engine = create_engine("sqlite://")
    try:
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
            db.add(models.AppRecord(id=214, name="Synthetic app", client_id="fixture-app-214",
                                   api_key_hash="synthetic-only"))
            db.add(models.PolicyRecord(id=210, policy_type="input", connector="github", action="create",
                                       resource="issue", effect="block", enabled=True,
                                       conditions={"custom_resource": LEGACY}, policy_version=1))
            db.flush()
            db.add(models.AppPolicyAssignmentRecord(app_id=214, policy_id=210,
                                                    display_name="Retained fixture label", enabled=True))
        with Session(engine) as db:
            record = db.get(models.PolicyRecord, 210)
            assignment = db.scalar(select(models.AppPolicyAssignmentRecord))
            before = {column.name: getattr(assignment, column.name) for column in assignment.__table__.columns}
            record.conditions = proposed
            record.policy_version += 1
            refresh_compiled_policy_rule(db, record)
            db.commit()
        with Session(engine) as db:
            record = db.get(models.PolicyRecord, 210)
            assignment = db.scalar(select(models.AppPolicyAssignmentRecord))
            assert before == {column.name: getattr(assignment, column.name) for column in assignment.__table__.columns}
            assert (record.id, record.enabled, record.effect, record.policy_version) == (210, True, "block", 2)
            assert record.conditions == proposed
            compiled = list(db.scalars(select(models.CompiledPolicyRuleRecord).where(
                models.CompiledPolicyRuleRecord.policy_id == 210,
                models.CompiledPolicyRuleRecord.enabled.is_(True),
                models.CompiledPolicyRuleRecord.stale.is_(False))))
            assert len(compiled) == 1 and 'test' in compiled[0].rule_text
    finally:
        engine.dispose()
    print("Synthetic policy 210 rehearsal passed; actual work database unchanged.")


if __name__ == "__main__":
    main()
