from dataclasses import dataclass
from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from fastapi.testclient import TestClient
from nemoguardrails.rails.llm.options import RailStatus, RailType
from sqlalchemy import select

import nemo_mcp_guardrails.api.runtime as runtime_api
from nemo_mcp_guardrails.api.main import app
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import (
    AppConnectorRecord,
    AppPolicyAssignmentRecord,
    AppRecord,
    CompiledPolicyRuleRecord,
    ConnectorRecord,
    PolicyRecord,
)
from nemo_mcp_guardrails.database.policy_loader import load_input_policy_entries
from nemo_mcp_guardrails.prompt_rule_compiler import (
    PromptRuleConfig,
    build_rails_config_with_prompt_rules,
)
from nemo_mcp_guardrails.tool_guard import blocked_tool_names_for_app
from seed_normalized_policy_metadata import main as seed_normalized_metadata


TEMP_API_KEY = "temporary-guardrails-run-api-key"
AGENT_CALLS: list[object] = []


@dataclass(frozen=True)
class FakeRuntimeParts:
    """Runtime parts built from real DB scope and fake rails/agent."""

    prompt_rule_config: PromptRuleConfig
    input_policy_count: int
    blocked_tools: frozenset[str]
    rails: object
    agent: object
    output_rail_enabled: bool


class FakeRailResult:
    """Small fake rail result for HTTP runtime integration tests."""

    def __init__(self, status: RailStatus, content: str = "") -> None:
        self.status = status
        self.content = content


class FakePolicyRails:
    """Fake rails that block the temporary GitHub issue creation policy."""

    async def check_async(
        self,
        messages: object,
        rail_types: object,
    ) -> FakeRailResult:
        rail_type_values = {str(rail_type) for rail_type in rail_types}
        if "RailType.INPUT" in rail_type_values:
            message_text = str(messages[0]["content"]).lower()
            if "create" in message_text and "issue" in message_text:
                return FakeRailResult(RailStatus.BLOCKED)

        return FakeRailResult(RailStatus.PASSED)


class FakeAgent:
    """Fake agent that records calls and reports one read-only GitHub tool."""

    async def ainvoke(self, payload: object) -> dict[str, object]:
        AGENT_CALLS.append(payload)
        return {
            "messages": [
                type(
                    "FakeMessage",
                    (),
                    {
                        "content": "github/github-mcp-server",
                        "name": "search_repositories",
                    },
                )()
            ]
        }


async def fake_build_guardrails_runtime_parts(app_id: int) -> FakeRuntimeParts:
    """Build fake runtime parts using real app-scoped DB loaders."""

    prompt_rule_config = build_rails_config_with_prompt_rules(
        "config",
        app_id=app_id,
    )
    blocked_tools = blocked_tool_names_for_app(app_id=app_id)

    return FakeRuntimeParts(
        prompt_rule_config=prompt_rule_config,
        input_policy_count=len(load_input_policy_entries(app_id=app_id)),
        blocked_tools=blocked_tools,
        rails=FakePolicyRails(),
        agent=FakeAgent(),
        output_rail_enabled=True,
    )


def count_policy_compiled_rules(policy_id: int) -> int:
    """Return active compiled rule count for one policy."""

    with SessionLocal() as db:
        return len(
            list(
                db.scalars(
                    select(CompiledPolicyRuleRecord).where(
                        CompiledPolicyRuleRecord.policy_id == policy_id,
                        CompiledPolicyRuleRecord.enabled.is_(True),
                        CompiledPolicyRuleRecord.stale.is_(False),
                    )
                )
            )
        )


def cleanup_records(app_id: int | None, policy_id: int | None) -> None:
    """Delete temporary app and policy records created by this test."""

    with SessionLocal() as db:
        if app_id is not None:
            app_record = db.get(AppRecord, app_id)
            if app_record:
                db.delete(app_record)

        if policy_id is not None:
            policy_record = db.get(PolicyRecord, policy_id)
            if policy_record:
                db.delete(policy_record)

        db.commit()


def link_app_to_github_connector(app_id: int) -> None:
    """Link one temporary app to the enabled GitHub connector."""

    with SessionLocal() as db:
        github_connector = db.scalar(
            select(ConnectorRecord).where(ConnectorRecord.name == "github")
        )
        assert github_connector is not None

        db.add(
            AppConnectorRecord(
                app_id=app_id,
                connector_id=github_connector.id,
                enabled=True,
            )
        )
        db.commit()


def main() -> None:
    """Verify authenticated /run uses app-scoped policies over HTTP."""

    seed_normalized_metadata()
    suffix = uuid4().hex
    target_issue_title = f"guardrails-test-{suffix}"
    client_id = f"guardrails-run-{suffix}"
    app_id: int | None = None
    policy_id: int | None = None
    original_builder = runtime_api.build_guardrails_runtime_parts

    try:
        runtime_api.build_guardrails_runtime_parts = (
            fake_build_guardrails_runtime_parts
        )

        with TestClient(app) as client:
            app_response = client.post(
                "/apps",
                json={
                    "name": f"Temporary Guardrails Run App {suffix}",
                    "client_id": client_id,
                    "api_key": TEMP_API_KEY,
                    "authorized": True,
                },
            )
            assert app_response.status_code == 201, app_response.text
            app_id = app_response.json()["id"]
            link_app_to_github_connector(app_id)

            policy_response = client.post(
                "/policies",
                json={
                    "policy_type": "input",
                    "connector": "github",
                    "action": "create",
                    "resource": "issue",
                    "effect": "block",
                    "conditions": {
                        "custom_resource": f'issue named "{target_issue_title}"'
                    },
                    "enabled": True,
                },
            )
            assert policy_response.status_code == 201, policy_response.text
            policy_id = policy_response.json()["id"]
            assert count_policy_compiled_rules(policy_id) == 1

            assignment_response = client.post(
                f"/apps/{app_id}/policy-assignments",
                json={"policy_ids": [policy_id], "enabled": True},
            )
            assert assignment_response.status_code == 201, assignment_response.text
            assert assignment_response.json()[0]["policy_id"] == policy_id

            allowed_response = client.post(
                "/v1/guardrails/run",
                headers={"X-App-ID": client_id, "X-API-Key": TEMP_API_KEY},
                json={
                    "conversation_id": f"allowed-{suffix}",
                    "message": (
                        "Use GitHub MCP to search repositories for "
                        "github/github-mcp-server."
                    ),
                },
            )
            assert allowed_response.status_code == 200, allowed_response.text
            allowed_body = allowed_response.json()
            assert allowed_body["status"] == "passed"
            assert allowed_body["app_id"] == app_id
            assert allowed_body["client_id"] == client_id
            assert allowed_body["response"] == "github/github-mcp-server"
            assert allowed_body["tool_names"] == ["search_repositories"]
            assert allowed_body["input_policy_count"] == 1
            assert allowed_body["input_rule_count"] == 1
            assert "issue_write" in allowed_body["blocked_tools"]

            blocked_response = client.post(
                "/v1/guardrails/run",
                headers={"X-App-ID": client_id, "X-API-Key": TEMP_API_KEY},
                json={
                    "conversation_id": f"blocked-{suffix}",
                    "message": (
                        f"Create a GitHub issue titled {target_issue_title} in "
                        "github/github-mcp-server."
                    ),
                },
            )
            assert blocked_response.status_code == 200, blocked_response.text
            blocked_body = blocked_response.json()
            assert blocked_body["status"] == "blocked"
            assert blocked_body["app_id"] == app_id
            assert blocked_body["client_id"] == client_id
            assert blocked_body["tool_names"] == []
            assert blocked_body["input_rail_status"] == "blocked"
            assert blocked_body["input_policy_count"] == 1
            assert blocked_body["input_rule_count"] == 1
            assert "issue_write" in blocked_body["blocked_tools"]

        assert len(AGENT_CALLS) == 1

        with SessionLocal() as db:
            assignment_count = len(
                list(
                    db.scalars(
                        select(AppPolicyAssignmentRecord).where(
                            AppPolicyAssignmentRecord.app_id == app_id
                        )
                    )
                )
            )
        assert assignment_count == 1

        print("Guardrails run HTTP integration checks passed.")
        print("- Temporary app authenticated with X-App-ID/X-API-Key.")
        print("- Policy create auto-compiled one active rule.")
        print("- App policy assignment scoped rules and blocked tools to /run.")
        print("- Allowed read request reached the fake agent.")
        print("- Blocked write request stopped before agent execution.")

    finally:
        runtime_api.build_guardrails_runtime_parts = original_builder
        cleanup_records(app_id, policy_id)
        AGENT_CALLS.clear()
        print("- Temporary guardrails-run records deleted")


if __name__ == "__main__":
    main()
