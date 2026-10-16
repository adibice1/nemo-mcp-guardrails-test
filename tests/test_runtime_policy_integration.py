"""Offline authenticated HTTP and cache checks for exact scoped enforcement."""

import asyncio
import json
import os
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Exercise real runtime coordination with SQLite and fake external boundaries."""

    with patch.dict(os.environ, {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "NEMO_POLICY_SOURCE": "database", "NEMO_RUNTIME_CACHE_TTL_SECONDS": "300",
        "NEMO_RUNTIME_DEBUG": "0", "GMS_ALLOWED_LLM_CREDENTIAL_ENV_VARS": "",
        "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com", "GMS_ALLOWED_LLM_ENDPOINTS": "",
    }):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from langchain_core.messages import AIMessage
        from nemoguardrails.rails.llm.options import RailStatus
        from sqlalchemy import JSON, MetaData, create_engine, select, update
        from sqlalchemy.dialects.postgresql import JSONB
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from nemo_mcp_guardrails import runtime_factory as factory
        from nemo_mcp_guardrails.api import runtime
        from nemo_mcp_guardrails.app_auth import hash_api_key
        from nemo_mcp_guardrails.database import models
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database.policy_errors import PolicyLoadError
        from nemo_mcp_guardrails.database.policy_loader import _to_input_policy_object
        from nemo_mcp_guardrails.policy_rule_service import compile_policy_rule_record
        from nemo_mcp_guardrails.runtime_events import capture_runtime_events
        from nemo_mcp_guardrails.tool_guard import ToolGuardRule

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
            connector = models.ConnectorRecord(name="github", display_name="GitHub")
            db.add(connector)
            db.flush()
            for app_id in (1, 2):
                db.add(models.AppRecord(id=app_id, client_id=f"app-{app_id}", name=f"App {app_id}",
                                        api_key_hash=hash_api_key("fake-key"), authorized=True))
                db.flush()
                db.add(models.AppConnectorRecord(app_id=app_id, connector_id=connector.id, enabled=True))
                db.add_all([models.AppLlmGrantRecord(app_id=app_id, purpose=purpose, enabled=True)
                            for purpose in ("main", "guardrail")])
            targeted = models.PolicyRecord(policy_type="input", connector="github", action="create", resource="issue",
                conditions={"custom_resource": 'title = "deploy!"', "resource_condition_version": 1})
            global_input = models.PolicyRecord(policy_type="input", connector="github", action="create", resource="repository", conditions={})
            output = models.PolicyRecord(policy_type="output", category="custom", conditions={"output_rule": 'Never include "restricted phrase".'})
            db.add_all([targeted, global_input, output])
            db.flush()
            targeted_id, global_id = targeted.id, global_input.id
            assignment = models.AppPolicyAssignmentRecord(app_id=1, policy_id=targeted.id)
            db.add_all([assignment, models.GlobalPolicyAssignmentRecord(policy_id=global_input.id),
                        models.GlobalPolicyAssignmentRecord(policy_id=output.id)])
            db.flush()
            assignment_id = assignment.id
            for policy in (targeted, global_input, output):
                db.add(compile_policy_rule_record(policy))

        def test_db():
            """Keep actual app-key authentication and history backed by real rows."""

            with sessions() as db:
                yield db

        def change_target(action="create", resource="issue", selector='title = "deploy!"', compile_rule=True):
            """Change exact contents atomically while preserving versions/timestamps."""

            with sessions.begin() as db:
                policy = db.get(models.PolicyRecord, targeted_id)
                artifact = db.scalar(select(models.CompiledPolicyRuleRecord).where(
                    models.CompiledPolicyRuleRecord.policy_id == targeted_id))
                timestamp, compiled_timestamp = policy.updated_at, artifact.updated_at
                policy.action, policy.resource = action, resource
                from nemo_mcp_guardrails.input_conditions import prepare_input_conditions
                from nemo_mcp_guardrails.policy_compiler import InputPolicyObject
                policy.conditions = prepare_input_conditions(InputPolicyObject("github", action, resource, "block"), {"custom_resource": selector}) if selector is not None else {}
                policy.updated_at = timestamp
                if compile_rule:
                    artifact.rule_text = compile_policy_rule_record(policy).rule_text
                    artifact.updated_at = compiled_timestamp

        calls, builds, executions, stored = [], [], [], []
        build_hook = None

        class RawTool:
            """Expose reviewed adapter-style schemas and record only actual invocations."""

            def __init__(self, name, properties):
                """Keep each independent fake schema compatible with the reviewed server."""

                self.name, self.description = name, "Offline tool"
                self.args_schema = {"type": "object", "properties": properties}

            async def ainvoke(self, arguments):
                """Record calls only after the real wrapper permits execution."""

                calls.append((self.name, arguments))
                return "Safe tool result."

        raw_tools = [
            RawTool("issue_write", {"method": {"type": "string", "enum": ["create", "update"]},
                "title": {"type": "string"}, "issue_number": {"type": "number"}}),
            RawTool("create_repository", {"name": {"type": "string"}, "autoInit": {"type": "boolean"}}),
            RawTool("fork_repository", {"repo": {"type": "string"}}),
            RawTool("delete_file", {"path": {"type": "string"}}),
            RawTool("merge_pull_request", {"pullNumber": {"type": "number"}}),
            RawTool("create_pull_request", {"title": {"type": "string"}, "head": {"type": "string"}, "base": {"type": "string"}}),
            RawTool("search_repositories", {}), RawTool("unreviewed_write", {}),
        ]

        class FakeClient:
            """Replace process startup while exercising real catalogue/wrapper construction."""

            def __init__(self, config):
                """Record builds without opening any transport."""

                builds.append(config)

            async def get_tools(self):
                """Allow controlled state changes while construction is in flight."""

                if build_hook is not None:
                    build_hook()
                return raw_tools

        class FakeRails:
            """Pass classification so deterministic tool/output checks are exercised."""

            def __init__(self, config, llm):
                """Accept the real snapshot-derived NeMo configuration."""

                self.config = config

            async def check_async(self, messages, rail_types):
                """Return a normal rail result without a model call."""

                return SimpleNamespace(status=RailStatus.PASSED, content=None)

        class FakeAgent:
            """Invoke the real guarded tool chosen by the test request."""

            def __init__(self, tools):
                """Keep only tools admitted by the real catalogue filter."""

                self.tools = {tool.name: tool for tool in tools}
                assert "unreviewed_write" not in self.tools

            async def ainvoke(self, payload):
                """Run one connector call through the actual wrapper and execution coordinator."""

                executions.append(True)
                request = json.loads(payload["messages"][-1]["content"])
                await self.tools[request["tool"]].ainvoke(request["arguments"])
                return {"messages": [AIMessage(content=request.get("answer", "Safe answer."))]}

        app = FastAPI()
        app.include_router(runtime.router)
        app.dependency_overrides[get_db] = test_db
        real_store = runtime._store_conversation_turns

        def record_store(*args, **kwargs):
            """Exercise actual conversation persistence and count reached storage boundaries."""

            stored.append(True)
            return real_store(*args, **kwargs)

        factory.clear_guardrails_runtime_cache()
        with ExitStack() as stack:
            stack.enter_context(patch.object(factory, "SessionLocal", sessions))
            stack.enter_context(patch("nemo_mcp_guardrails.prompt_rule_compiler.load_prompt_policy_rules",
                side_effect=AssertionError("Separate prompt-rule read")))
            stack.enter_context(patch("nemo_mcp_guardrails.tool_guard.load_input_policy_entries",
                side_effect=AssertionError("Separate tool-policy read")))
            stack.enter_context(patch.object(factory, "load_runtime_revision", return_value=("constant",)))
            stack.enter_context(patch.object(factory, "load_runtime_environment", return_value=factory.RuntimeEnvironment(
                "fake", "https://example.openai.azure.com", "fake", "fake", "fake", "1")))
            model = stack.enter_context(patch.object(factory, "build_chat_model", return_value=object()))
            stack.enter_context(patch.object(factory, "LLMRails", FakeRails))
            stack.enter_context(patch.object(factory, "MultiServerMCPClient", FakeClient))
            stack.enter_context(patch.object(factory, "create_agent", side_effect=lambda model, tools: FakeAgent(tools)))
            stack.enter_context(patch.object(runtime, "_store_conversation_turns", side_effect=record_store))
            client = stack.enter_context(TestClient(app))

            def run(tool="issue_write", arguments=None, app_id=1, expected="passed", answer=None):
                """Assert HTTP results, privacy, event reasons and pre-execution refusal."""

                before = (len(calls), len(executions), len(stored), model.call_count)
                message = {"tool": tool, "arguments": arguments if arguments is not None else {"method": "create", "title": "other"}}
                if answer is not None:
                    message["answer"] = answer
                with capture_runtime_events() as events:
                    response = client.post("/v1/guardrails/run", headers={"X-App-ID": f"app-{app_id}", "X-API-Key": "fake-key"},
                        json={"message": json.dumps(message), "conversation_id": "snapshot-test"})
                assert response.status_code == (503 if expected == "unavailable" else 200), response.text
                assert "PRIVATE" not in response.text
                assert "PRIVATE" not in json.dumps(events, default=str)
                if expected == "unavailable":
                    assert (len(calls), len(executions), len(stored)) == before[:3]
                else:
                    assert response.json()["status"] == expected, response.text
                    if expected in {"blocked", "tool_error"} and answer is None:
                        assert len(calls) == before[0]
                        assert not any(event["event"] == "tool.started" for event in events)
                    if expected == "tool_error":
                        assert response.json()["tool_guard_source"] == "gms_tool_guard_evaluation"
                        assert response.json()["blocked_policy_id"] is None
                        assert any(event["reason_code"] == "gms_tool_guard_evaluation" for event in events)
                return response.json()

            blocked = run(arguments={"method": "create", "title": "Deploy!"}, expected="blocked")
            assert blocked["blocked_policy_id"] == targeted_id
            assert blocked["blocked_policy_name"] == "GitHub create issue"
            run(arguments={"method": "create", "title": "other", "body": "Deploy!"})
            run(arguments={"method": "update", "title": "Deploy!", "issue_number": 42})
            run(arguments={"method": "create", "body": "PRIVATE_ARGUMENT"}, expected="tool_error")
            assert len(builds) == 1
            parts = factory._RUNTIME_PARTS_CACHE[1].parts
            assert {entry.source_id for entry in parts.input_policy_entries} == {targeted_id, global_id}
            assert parts.prompt_rule_config.input_rule_count == 2 and parts.prompt_rule_config.output_rule_count == 1
            assert parts.blocked_output_phrases == ("restricted phrase",)
            run("search_repositories", {}, expected="blocked", answer="restricted phrase")
            for app_id in (1, 2):
                assert run("create_repository", {"name": "example"}, app_id, "blocked")["blocked_policy_id"] == global_id
            run(arguments={"method": "create", "title": "Deploy!"}, app_id=2)
            with sessions.begin() as db:
                db.execute(update(models.AppPolicyAssignmentRecord).where(models.AppPolicyAssignmentRecord.id == assignment_id).values(enabled=False))
            run(arguments={"method": "create", "title": "Deploy!"})
            with sessions.begin() as db:
                db.execute(update(models.AppPolicyAssignmentRecord).where(models.AppPolicyAssignmentRecord.id == assignment_id).values(enabled=True))
            run(arguments={"method": "create", "title": "Deploy!"}, expected="blocked")
            change_target("delete", "file", 'path = "src/Auth.py"')
            run("delete_file", {"path": "src/Auth.py"}, expected="blocked")
            run("delete_file", {"path": "src/auth.py", "message": "src/Auth.py"})
            run("merge_pull_request", {"pullNumber": 42, "path": "src/Auth.py"}, expected="tool_error")
            change_target("delete", "file", 'path = "src/auth.py"')
            run("delete_file", {"path": "src/Auth.py"})
            run("delete_file", {"path": "src/auth.py"}, expected="blocked")
            change_target("update", "pull_request", None)
            shared = run(arguments={"method": "update", "issue_number": 42}, expected="blocked")
            assert shared["blocked_policy_id"] == targeted_id and shared["blocked_policy_name"] == "GitHub update pull request"
            run(arguments={"method": "create", "title": "other"})
            route = 'source_branch != "staging" AND target_branch = "production"'
            change_target("create", "pull_request", route)
            route_block = run("create_pull_request", {"head": "feature", "base": "production"}, expected="blocked")
            assert route_block["blocked_policy_id"] == targeted_id
            run("create_pull_request", {"head": "staging", "base": "production"})
            run("create_pull_request", {"head": "feature", "base": "production"}, app_id=2)
            previous_builds = len(builds)
            change_target("create", "pull_request", 'source_branch != "release" AND target_branch = "production"')
            run("create_pull_request", {"head": "staging", "base": "production"}, expected="blocked")
            assert len(builds) > previous_builds  # Exact branch content invalidates warm cache.
            change_target("merge", "pull_request", route)
            run("merge_pull_request", {"pullNumber": 42, "head": "staging", "base": "development"}, expected="tool_error")
            change_target(selector='title = "new"', compile_rule=False)
            run(expected="unavailable")
            change_target()
            with patch.object(factory, "read_runtime_policy_snapshot", side_effect=PolicyLoadError("PRIVATE_DB")):
                run(expected="unavailable")
            with sessions.begin() as db:
                db.get(models.PolicyRecord, targeted_id).conditions = {"custom_resource": "legacy"}
            run(expected="unavailable")
            change_target()
            with sessions.begin() as db:
                db.execute(update(models.CompiledPolicyRuleRecord).where(models.CompiledPolicyRuleRecord.policy_id == targeted_id).values(stale=True))
            run(expected="unavailable")
            with sessions.begin() as db:
                db.execute(update(models.CompiledPolicyRuleRecord).where(models.CompiledPolicyRuleRecord.policy_id == targeted_id).values(stale=False))
                db.execute(update(models.CompiledPolicyRuleRecord).where(models.CompiledPolicyRuleRecord.policy_id == global_id).values(stale=True))
            for app_id in (1, 2):
                run(app_id=app_id, expected="unavailable")
            with sessions.begin() as db:
                db.execute(update(models.CompiledPolicyRuleRecord).where(models.CompiledPolicyRuleRecord.policy_id == global_id).values(stale=False))
            factory.clear_guardrails_runtime_cache()
            raw_tools[0].args_schema["properties"]["method"]["enum"].append("unreviewed")
            run(expected="unavailable")
            raw_tools[0].args_schema["properties"]["method"]["enum"].remove("unreviewed")
            for ttl in ("300", "0"):
                factory.clear_guardrails_runtime_cache()
                build_hook = lambda: change_target(selector='title = "changed-during-build"')
                with patch.dict(os.environ, {"NEMO_RUNTIME_CACHE_TTL_SECONDS": ttl}):
                    run(expected="unavailable")
                assert 1 not in factory._RUNTIME_PARTS_CACHE
                build_hook = None
                change_target()
            with patch.dict(os.environ, {"NEMO_RUNTIME_CACHE_TTL_SECONDS": "0"}):
                before = len(builds)
                run(); run()
                assert len(builds) == before + 2
            with sessions.begin() as db:
                db.execute(update(models.GlobalPolicyAssignmentRecord).values(enabled=False))
            empty = run("search_repositories", {}, app_id=2)
            assert empty["input_policy_count"] == empty["input_rule_count"] == empty["output_rule_count"] == 0
            with sessions.begin() as db:
                db.execute(update(models.GlobalPolicyAssignmentRecord).values(enabled=True))

            async def lock_race():
                """Reject changed policy state after waiting on an existing build lock."""

                factory.clear_guardrails_runtime_cache()
                lock = asyncio.Lock()
                await lock.acquire()
                factory._RUNTIME_BUILD_LOCKS[1] = lock
                before = len(builds)
                task = asyncio.create_task(factory.build_guardrails_runtime_parts(1))
                await asyncio.sleep(0)
                with sessions.begin() as db:
                    db.get(models.PolicyRecord, targeted_id).conditions = {"custom_resource": "legacy"}
                lock.release()
                try:
                    await task
                except PolicyLoadError:
                    pass
                else:
                    raise AssertionError("Lock-wait change was ignored")
                assert len(builds) == before

            asyncio.run(lock_race())
            change_target()

            async def node_errors():
                """Prove the installed agent tool node propagates both guard error kinds."""

                from langgraph.prebuilt import ToolNode
                from langgraph.graph import END, START, MessagesState, StateGraph
                from nemo_mcp_guardrails.tool_guard import ToolGuardEvaluationError, ToolGuardViolation

                parts = await factory.build_guardrails_runtime_parts(1)
                graph = StateGraph(MessagesState)
                graph.add_node("tools", ToolNode(list(parts.tool_bundle.tools)))
                graph.add_edge(START, "tools")
                graph.add_edge("tools", END)
                node = graph.compile()
                before = len(calls)
                for arguments, error_type in (({"method": "create", "title": "Deploy!"}, ToolGuardViolation),
                                               ({"method": "create"}, ToolGuardEvaluationError)):
                    try:
                        await node.ainvoke({"messages": [AIMessage(content="", tool_calls=[{
                            "name": "issue_write", "args": arguments, "id": "offline-call",
                        }])]})
                    except error_type:
                        pass
                    else:
                        raise AssertionError("Agent tool node swallowed a guard failure")
                assert len(calls) == before

            asyncio.run(node_errors())
            with sessions() as db:
                try:
                    _to_input_policy_object(models.PolicyRecord(connector="github", action="create", resource="issue", effect="block",
                        conditions={"custom_resource": "legacy"}))
                except PolicyLoadError:
                    pass
                else:
                    raise AssertionError("Legacy diagnostic loader accepted an unreviewed selector")
            try:
                ToolGuardRule(frozenset({"issue_write"}), "legacy")
            except ValueError:
                pass
            else:
                raise AssertionError("Legacy conditional wrapper remained available")
            factory.clear_guardrails_runtime_cache()
        engine.dispose()
        print("Runtime policy integration passed: authenticated HTTP, scoped snapshots, field guards, exact cache changes and build races.")


if __name__ == "__main__":
    main()
