from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import select
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.app_auth import hash_api_key
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import (
    AppPolicyAssignmentRecord,
    AppRecord,
    PolicyRecord,
)
from nemo_mcp_guardrails.database.policy_loader import load_input_policy_objects
from nemo_mcp_guardrails.prompt_rule_compiler import (
    build_rails_config_with_prompt_rules,
)
from nemo_mcp_guardrails.tool_guard import blocked_tool_names_for_app


def policy_names(record: PolicyRecord) -> tuple[str | None, str | None, str | None]:
    """Return normalized policy names with compatibility-field fallbacks."""

    connector = (
        record.normalized_connector.name
        if record.normalized_connector
        else record.connector
    )
    action = record.normalized_action.name if record.normalized_action else record.action
    resource = (
        record.normalized_resource.name
        if record.normalized_resource
        else record.resource
    )
    return connector, action, resource


def find_issue_creation_policy(db: Session) -> PolicyRecord:
    """Return the enabled GitHub issue-creation input policy."""

    policies = db.scalars(
        select(PolicyRecord).where(
            PolicyRecord.policy_type == "input",
            PolicyRecord.enabled.is_(True),
        )
    )
    for policy in policies:
        if policy_names(policy) == ("github", "create", "issue"):
            return policy

    raise RuntimeError("Missing enabled github/create/issue input policy")


def create_temporary_apps() -> tuple[int, int, int]:
    """Create two temporary apps and assign issue creation only to App A."""

    suffix = uuid4().hex
    fake_hash = hash_api_key("temporary-test-key")

    with SessionLocal() as db:
        issue_policy = find_issue_creation_policy(db)
        app_a = AppRecord(
            name="Temporary Scope Test App A",
            client_id=f"scope-test-a-{suffix}",
            api_key_hash=fake_hash,
            authorized=True,
        )
        app_b = AppRecord(
            name="Temporary Scope Test App B",
            client_id=f"scope-test-b-{suffix}",
            api_key_hash=fake_hash,
            authorized=True,
        )
        db.add_all([app_a, app_b])
        db.flush()

        db.add(
            AppPolicyAssignmentRecord(
                app_id=app_a.id,
                policy_id=issue_policy.id,
                enabled=True,
            )
        )
        db.commit()
        return app_a.id, app_b.id, issue_policy.id


def delete_temporary_apps(app_ids: tuple[int, int]) -> None:
    """Delete temporary apps and their cascading policy assignments."""

    with SessionLocal() as db:
        for app_id in app_ids:
            app = db.get(AppRecord, app_id)
            if app:
                db.delete(app)
        db.commit()


def main() -> None:
    """Verify real DB app assignments scope NeMo rules and blocked tools."""

    app_a_id, app_b_id, issue_policy_id = create_temporary_apps()

    try:
        app_a_policies = load_input_policy_objects(app_id=app_a_id)
        app_b_policies = load_input_policy_objects(app_id=app_b_id)
        app_a_tools = blocked_tool_names_for_app(app_id=app_a_id)
        app_b_tools = blocked_tool_names_for_app(app_id=app_b_id)
        app_a_config = build_rails_config_with_prompt_rules(
            "config",
            app_id=app_a_id,
        )
        app_b_config = build_rails_config_with_prompt_rules(
            "config",
            app_id=app_b_id,
        )

        assert len(app_a_policies) == 1
        assert app_b_policies == ()
        assert "issue_write" in app_a_tools
        assert "issue_write" not in app_b_tools

        app_a_input_policy_ids = {
            rule.policy_id
            for rule in app_a_config.prompt_rules
            if rule.rail_type == "input"
        }
        app_b_input_policy_ids = {
            rule.policy_id
            for rule in app_b_config.prompt_rules
            if rule.rail_type == "input"
        }
        app_a_output_policy_ids = {
            rule.policy_id
            for rule in app_a_config.prompt_rules
            if rule.rail_type == "output"
        }
        app_b_output_policy_ids = {
            rule.policy_id
            for rule in app_b_config.prompt_rules
            if rule.rail_type == "output"
        }

        assert issue_policy_id in app_a_input_policy_ids
        assert issue_policy_id not in app_b_input_policy_ids
        assert app_a_output_policy_ids
        assert app_a_output_policy_ids == app_b_output_policy_ids

        print("App policy scope integration checks passed.")
        print(f"- App A #{app_a_id}: issue_write blocked")
        print(f"- App B #{app_b_id}: issue_write allowed")
        print("- Both apps received the same global output policies")
    finally:
        delete_temporary_apps((app_a_id, app_b_id))
        print("- Temporary apps and assignments deleted")


if __name__ == "__main__":
    main()
