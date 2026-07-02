import asyncio
import os
from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from fastapi.testclient import TestClient
from langchain_core.tools import ToolException
from nemoguardrails.exceptions import LLMCallException
from nemoguardrails.rails.llm.options import RailStatus
from openai import BadRequestError
from sqlalchemy import select

import nemo_mcp_guardrails.api.runtime as runtime_api
from nemo_mcp_guardrails.api.main import app
from nemo_mcp_guardrails.app_auth import hash_api_key
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import AppRecord, ConversationMessageRecord
from nemo_mcp_guardrails.guarded_execution import (
    OUTPUT_FILTER_RESPONSE,
    TOOL_ERROR_RESPONSE,
    GuardedExecutionResult,
    execute_guarded_message,
)
from nemo_mcp_guardrails.tool_guard import TOOL_GUARD_REFUSAL, ToolGuardViolation


VALID_API_KEY = "temporary-valid-http-api-key"
INVALID_RESPONSE = {"detail": "Invalid app credentials"}
EXECUTION_CALLS: list[dict[str, object]] = []


def create_temporary_apps() -> tuple[int, int, str, str]:
    """Create authorized and unauthorized temporary HTTP-test apps."""

    suffix = uuid4().hex
    authorized_client_id = f"http-auth-authorized-{suffix}"
    unauthorized_client_id = f"http-auth-unauthorized-{suffix}"

    with SessionLocal() as db:
        authorized_app = AppRecord(
            name="Temporary HTTP Authorized App",
            client_id=authorized_client_id,
            api_key_hash=hash_api_key(VALID_API_KEY),
            authorized=True,
        )
        unauthorized_app = AppRecord(
            name="Temporary HTTP Unauthorized App",
            client_id=unauthorized_client_id,
            api_key_hash=hash_api_key(VALID_API_KEY),
            authorized=False,
        )
        db.add_all([authorized_app, unauthorized_app])
        db.commit()
        db.refresh(authorized_app)
        db.refresh(unauthorized_app)

        return (
            authorized_app.id,
            unauthorized_app.id,
            authorized_client_id,
            unauthorized_client_id,
        )


def delete_temporary_apps(app_ids: tuple[int, int]) -> None:
    """Delete temporary HTTP authentication-test apps."""

    with SessionLocal() as db:
        for app_id in app_ids:
            app_record = db.get(AppRecord, app_id)
            if app_record:
                db.delete(app_record)
        db.commit()


class FakePromptRuleConfig:
    """Small prompt-rule config substitute for HTTP runtime tests."""

    input_rule_count = 0
    output_rule_count = 1


class FakeRuntimeParts:
    """Small runtime substitute so HTTP auth tests do not start Docker or Azure."""

    prompt_rule_config = FakePromptRuleConfig()
    input_policy_count = 0
    blocked_tools = frozenset()
    rails = object()
    agent = object()
    output_rail_enabled = True
    blocked_output_phrases: tuple[str, ...] = ()


async def fake_build_guardrails_runtime_parts(app_id: int) -> FakeRuntimeParts:
    """Return fake runtime parts after authentication has succeeded."""

    return FakeRuntimeParts()


async def fake_execute_guarded_message(**kwargs: object) -> GuardedExecutionResult:
    """Return a fake guarded result for the protected HTTP runtime test."""

    EXECUTION_CALLS.append(kwargs)
    return GuardedExecutionResult(
        status="passed",
        response="fake guarded response",
        input_rail_status=RailStatus.PASSED,
        output_rail_status=RailStatus.PASSED,
        tool_names=("search_repositories",),
        agent_result=None,
        input_rail_result=None,
        output_rail_result=None,
        raw_agent_response="fake guarded response",
        output_rail_source="nemo_passed",
    )


class FakeRailResult:
    """Small fake rail result for guarded execution tests."""

    def __init__(self, status: RailStatus, content: str = "") -> None:
        self.status = status
        self.content = content


class FakeRails:
    """Fake rails object that passes input and output checks."""

    async def check_async(self, messages: object, rail_types: object) -> FakeRailResult:
        return FakeRailResult(RailStatus.PASSED)


class FakeOutputFilterRails:
    """Fake rails object that simulates Azure filtering output self-checks."""

    async def check_async(self, messages: object, rail_types: object) -> FakeRailResult:
        rail_type_values = {str(rail_type) for rail_type in rail_types}
        if "RailType.OUTPUT" in rail_type_values:
            raise LLMCallException(
                BadRequestError(
                    "content filter",
                    response=type(
                        "FakeResponse",
                        (),
                        {
                            "request": None,
                            "status_code": 400,
                            "headers": {},
                            "text": "content filter",
                            "json": lambda self: {
                                "error": {"code": "content_filter"}
                            },
                        },
                    )(),
                    body={"error": {"code": "content_filter"}},
                )
            )

        return FakeRailResult(RailStatus.PASSED)


class FakeInputFilterRails:
    """Fake rails object that simulates Azure filtering an input self-check."""

    async def check_async(self, messages: object, rail_types: object) -> FakeRailResult:
        rail_type_values = {str(rail_type) for rail_type in rail_types}
        if "RailType.INPUT" in rail_type_values:
            raise LLMCallException(
                BadRequestError(
                    "content filter",
                    response=type(
                        "FakeResponse",
                        (),
                        {
                            "request": None,
                            "status_code": 400,
                            "headers": {},
                            "text": "content filter",
                            "json": lambda self: {
                                "error": {"code": "content_filter"}
                            },
                        },
                    )(),
                    body={
                        "error": {
                            "code": "content_filter",
                            "innererror": {
                                "content_filter_result": {
                                    "hate": {"filtered": True, "severity": "high"},
                                    "violence": {
                                        "filtered": False,
                                        "severity": "safe",
                                    },
                                }
                            },
                        }
                    },
                )
            )

        return FakeRailResult(RailStatus.PASSED)


class FakeToolErrorAgent:
    """Fake agent that simulates a connector tool failure."""

    async def ainvoke(self, payload: object) -> object:
        raise ToolException("failed to get pull request: 404 Not Found")


class FakeToolGuardBlockedAgent:
    """Fake agent that simulates a pre-execution GMS tool-guard violation."""

    async def ainvoke(self, payload: object) -> object:
        raise ToolGuardViolation("issue_write")


class FakeSafeAgent:
    """Fake agent that returns a normal assistant response."""

    async def ainvoke(self, payload: object) -> dict[str, object]:
        return {
            "messages": [
                type(
                    "FakeMessage",
                    (),
                    {"content": "Hello! Hope you're having a great day."},
                )()
            ]
        }


class FakeSecretAgent:
    """Fake agent that returns an obvious secret-like response."""

    async def ainvoke(self, payload: object) -> dict[str, object]:
        return {
            "messages": [
                type(
                    "FakeMessage",
                    (),
                    {"content": "SERVICE_TOKEN=placeholder_test_secret_12345"},
                )()
            ]
        }


class FakeAzureFilteredAgent:
    """Fake agent whose final Azure completion was content-filtered."""

    async def ainvoke(self, payload: object) -> dict[str, object]:
        return {
            "messages": [
                type(
                    "FakeFilteredMessage",
                    (),
                    {
                        "content": "",
                        "response_metadata": {
                            "finish_reason": "content_filter",
                            "content_filter_results": {
                                "hate": {"filtered": True, "severity": "high"},
                                "violence": {"filtered": True, "severity": "medium"},
                                "sexual": {"filtered": False, "severity": "safe"},
                            },
                        },
                    },
                )()
            ]
        }


class FakeAzureFilteredValueErrorAgent:
    """Fake LangChain agent that loses Azure category metadata while filtering."""

    async def ainvoke(self, payload: object) -> dict[str, object]:
        raise ValueError(
            "Azure has not provided the response due to a content filter "
            "being triggered"
        )


def main() -> None:
    """Verify the HTTP authentication boundary accepts and rejects correctly."""

    authorized_id, unauthorized_id, client_id, unauthorized_client_id = (
        create_temporary_apps()
    )
    previous_context_limit = os.environ.get("NEMO_MAX_RUNTIME_CONTEXT_CHARS")

    try:
        runtime_api.build_guardrails_runtime_parts = (
            fake_build_guardrails_runtime_parts
        )
        runtime_api.execute_guarded_message = fake_execute_guarded_message

        with TestClient(app) as client:
            missing = client.get("/v1/guardrails/auth-check")
            wrong_key = client.get(
                "/v1/guardrails/auth-check",
                headers={
                    "X-App-ID": client_id,
                    "X-API-Key": "wrong-api-key",
                },
            )
            unknown = client.get(
                "/v1/guardrails/auth-check",
                headers={
                    "X-App-ID": "unknown-client-id",
                    "X-API-Key": VALID_API_KEY,
                },
            )
            unauthorized = client.get(
                "/v1/guardrails/auth-check",
                headers={
                    "X-App-ID": unauthorized_client_id,
                    "X-API-Key": VALID_API_KEY,
                },
            )
            valid = client.get(
                "/v1/guardrails/auth-check",
                headers={
                    "X-App-ID": client_id,
                    "X-API-Key": VALID_API_KEY,
                },
            )
            run_missing = client.post(
                "/v1/guardrails/run",
                json={"message": "Summarize the repository."},
            )
            run_valid = client.post(
                "/v1/guardrails/run",
                headers={
                    "X-App-ID": client_id,
                    "X-API-Key": VALID_API_KEY,
                },
                json={"message": "Summarize the repository."},
            )
            conversation_id = f"conversation-{uuid4().hex}"
            run_with_history = client.post(
                "/v1/guardrails/run",
                headers={
                    "X-App-ID": client_id,
                    "X-API-Key": VALID_API_KEY,
                },
                json={
                    "message": "What about the second PR?",
                    "conversation_id": conversation_id,
                    "conversation_history": [
                        {"role": "user", "content": "List recent PRs."},
                        {"role": "assistant", "content": "PR #1 and PR #2."},
                    ],
                },
            )
            run_with_stored_history = client.post(
                "/v1/guardrails/run",
                headers={
                    "X-App-ID": client_id,
                    "X-API-Key": VALID_API_KEY,
                },
                json={
                    "message": "What did I ask about?",
                    "conversation_id": conversation_id,
                },
            )

            os.environ["NEMO_MAX_RUNTIME_CONTEXT_CHARS"] = "50"
            run_with_truncated_history = client.post(
                "/v1/guardrails/run",
                headers={
                    "X-App-ID": client_id,
                    "X-API-Key": VALID_API_KEY,
                },
                json={
                    "message": "ok",
                    "conversation_history": [
                        {"role": "user", "content": "a" * 20},
                        {"role": "assistant", "content": "b" * 20},
                        {"role": "user", "content": "c" * 20},
                    ],
                },
            )
            run_oversized_message = client.post(
                "/v1/guardrails/run",
                headers={
                    "X-App-ID": client_id,
                    "X-API-Key": VALID_API_KEY,
                },
                json={"message": "x" * 51},
            )

        for response in (missing, wrong_key, unknown, unauthorized, run_missing):
            assert response.status_code == 401
            assert response.json() == INVALID_RESPONSE

        assert valid.status_code == 200
        assert valid.json() == {
            "status": "authenticated",
            "app_id": authorized_id,
            "client_id": client_id,
        }
        assert run_valid.status_code == 200
        run_result = run_valid.json()
        assert run_result["status"] == "passed"
        assert run_result["app_id"] == authorized_id
        assert run_result["client_id"] == client_id
        assert run_result["response"] == "fake guarded response"
        assert run_result["input_rail_status"] == "passed"
        assert run_result["output_rail_status"] == "passed"
        assert run_result["output_rail_source"] == "nemo_passed"
        assert run_result["output_rail_categories"] == []
        assert run_result["tool_names"] == ["search_repositories"]
        assert run_result["input_policy_count"] == 0
        assert run_result["input_rule_count"] == 0
        assert run_result["output_rule_count"] == 1
        assert run_result["blocked_tools"] == []
        assert run_result["history_truncated"] is False
        assert run_result["history_messages_received"] == 0
        assert run_result["history_messages_loaded"] == 0
        assert run_result["history_messages_used"] == 0

        assert run_with_history.status_code == 200
        history_result = run_with_history.json()
        assert history_result["history_truncated"] is False
        assert history_result["history_messages_received"] == 2
        assert history_result["history_messages_loaded"] == 0
        assert history_result["history_messages_used"] == 2

        assert run_with_stored_history.status_code == 200
        stored_history_result = run_with_stored_history.json()
        assert stored_history_result["history_truncated"] is False
        assert stored_history_result["history_messages_received"] == 0
        assert stored_history_result["history_messages_loaded"] == 4
        assert stored_history_result["history_messages_used"] == 4

        assert run_with_truncated_history.status_code == 200
        truncated_result = run_with_truncated_history.json()
        assert truncated_result["history_truncated"] is True
        assert truncated_result["history_messages_received"] == 3
        assert truncated_result["history_messages_loaded"] == 0
        assert truncated_result["history_messages_used"] == 1

        assert run_oversized_message.status_code == 413
        assert "latest message has 51 characters" in run_oversized_message.json()[
            "detail"
        ]

        with SessionLocal() as db:
            stored_records = list(
                db.scalars(
                    select(ConversationMessageRecord)
                    .where(
                        ConversationMessageRecord.app_id == authorized_id,
                        ConversationMessageRecord.conversation_id == conversation_id,
                    )
                    .order_by(ConversationMessageRecord.id)
                )
            )
        assert [(record.role, record.content) for record in stored_records] == [
            ("user", "List recent PRs."),
            ("assistant", "PR #1 and PR #2."),
            ("user", "What about the second PR?"),
            ("assistant", "fake guarded response"),
            ("user", "What did I ask about?"),
            ("assistant", "fake guarded response"),
        ]
        assert len(EXECUTION_CALLS) == 4
        assert len(EXECUTION_CALLS[1]["conversation_history"]) == 2
        assert len(EXECUTION_CALLS[2]["conversation_history"]) == 4
        assert len(EXECUTION_CALLS[3]["conversation_history"]) == 1

        tool_error_result = asyncio.run(
            execute_guarded_message(
                rails=FakeRails(),
                agent=FakeToolErrorAgent(),
                message="What about PR #123?",
                output_rail_enabled=True,
            )
        )
        assert tool_error_result.status == "tool_error"
        assert tool_error_result.response == TOOL_ERROR_RESPONSE
        assert tool_error_result.input_rail_status == RailStatus.PASSED
        assert tool_error_result.output_rail_status == RailStatus.PASSED
        assert tool_error_result.tool_guard_status == "passed"

        tool_guard_result = asyncio.run(
            execute_guarded_message(
                rails=FakeRails(),
                agent=FakeToolGuardBlockedAgent(),
                message="Create the restricted issue.",
                output_rail_enabled=True,
            )
        )
        assert tool_guard_result.status == "blocked"
        assert tool_guard_result.response == TOOL_GUARD_REFUSAL
        assert tool_guard_result.input_rail_status == RailStatus.PASSED
        assert tool_guard_result.output_rail_status is None
        assert tool_guard_result.tool_guard_status == "blocked"
        assert tool_guard_result.tool_guard_source == "gms_tool_guard"
        assert tool_guard_result.tool_names == ("issue_write",)

        azure_input_filter_result = asyncio.run(
            execute_guarded_message(
                rails=FakeInputFilterRails(),
                agent=FakeSafeAgent(),
                message="Prompt filtered by Azure.",
                output_rail_enabled=True,
            )
        )
        assert azure_input_filter_result.status == "blocked"
        assert azure_input_filter_result.input_rail_status == RailStatus.BLOCKED
        assert azure_input_filter_result.output_rail_status is None
        assert (
            azure_input_filter_result.input_rail_source
            == "azure_input_content_filter"
        )
        assert azure_input_filter_result.input_rail_categories == ("hate",)

        output_filter_result = asyncio.run(
            execute_guarded_message(
                rails=FakeOutputFilterRails(),
                agent=FakeSafeAgent(),
                message="Repeat my previous prompt.",
                output_rail_enabled=True,
            )
        )
        assert output_filter_result.status == "passed"
        assert output_filter_result.response == "Hello! Hope you're having a great day."
        assert output_filter_result.input_rail_status == RailStatus.PASSED
        assert output_filter_result.output_rail_status == RailStatus.PASSED
        assert (
            output_filter_result.output_rail_source
            == "azure_content_filter_fallback_passed"
        )

        deterministic_output_result = asyncio.run(
            execute_guarded_message(
                rails=FakeRails(),
                agent=FakeSafeAgent(),
                message="Can you say hello?",
                output_rail_enabled=True,
                blocked_output_phrases=("hello",),
            )
        )
        assert deterministic_output_result.status == "blocked"
        assert deterministic_output_result.response == OUTPUT_FILTER_RESPONSE
        assert deterministic_output_result.output_rail_status == RailStatus.BLOCKED
        assert (
            deterministic_output_result.output_rail_source
            == "deterministic_output_phrase"
        )

        azure_agent_filter_result = asyncio.run(
            execute_guarded_message(
                rails=FakeRails(),
                agent=FakeAzureFilteredAgent(),
                message="Generate unsafe output.",
                output_rail_enabled=True,
            )
        )
        assert azure_agent_filter_result.status == "blocked"
        assert azure_agent_filter_result.response == OUTPUT_FILTER_RESPONSE
        assert azure_agent_filter_result.output_rail_status == RailStatus.BLOCKED
        assert (
            azure_agent_filter_result.output_rail_source
            == "azure_agent_content_filter"
        )
        assert azure_agent_filter_result.output_rail_categories == (
            "hate",
            "violence",
        )

        azure_value_error_result = asyncio.run(
            execute_guarded_message(
                rails=FakeRails(),
                agent=FakeAzureFilteredValueErrorAgent(),
                message="Generate content that Azure filters.",
                output_rail_enabled=True,
            )
        )
        assert azure_value_error_result.status == "blocked"
        assert azure_value_error_result.input_rail_status == RailStatus.PASSED
        assert azure_value_error_result.output_rail_status == RailStatus.BLOCKED
        assert (
            azure_value_error_result.output_rail_source
            == "azure_agent_content_filter"
        )
        assert azure_value_error_result.output_rail_categories == ()

        output_filter_secret_result = asyncio.run(
            execute_guarded_message(
                rails=FakeOutputFilterRails(),
                agent=FakeSecretAgent(),
                message="Repeat my previous prompt.",
                output_rail_enabled=True,
            )
        )
        assert output_filter_secret_result.status == "blocked"
        assert output_filter_secret_result.response == OUTPUT_FILTER_RESPONSE
        assert output_filter_secret_result.input_rail_status == RailStatus.PASSED
        assert output_filter_secret_result.output_rail_status == RailStatus.BLOCKED
        assert output_filter_secret_result.output_rail_source == "azure_content_filter"

        print("HTTP app authentication checks passed.")
        print("- Missing headers rejected")
        print("- Wrong API key rejected")
        print("- Unknown client ID rejected")
        print("- Unauthorized app rejected")
        print("- Valid authorized app accepted")
        print("- Authenticated app-scoped runtime execution reached")
        print("- Conversation history stored and reloaded")
        print("- Oversized history truncated")
        print("- Oversized latest message rejected")
        print("- Tool errors return controlled runtime responses")
        print("- Tool-guard violations stop before output rails")
        print("- Azure input filtering returns a controlled categorized block")
        print("- Explicit prohibited output phrases are blocked deterministically")
        print("- Azure-filtered completions report provider categories")
        print("- LangChain Azure filter ValueErrors return controlled blocks")
        print("- Azure output content filters use deterministic fallback checks")
    finally:
        if previous_context_limit is None:
            os.environ.pop("NEMO_MAX_RUNTIME_CONTEXT_CHARS", None)
        else:
            os.environ["NEMO_MAX_RUNTIME_CONTEXT_CHARS"] = previous_context_limit
        delete_temporary_apps((authorized_id, unauthorized_id))
        print("- Temporary HTTP authentication-test apps deleted")


if __name__ == "__main__":
    main()
