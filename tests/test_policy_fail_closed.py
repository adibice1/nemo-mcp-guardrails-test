"""Offline checks for mandatory policy loading and runtime setup failures."""

import asyncio
import importlib
import os
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Use disposable SQLite and mocked external boundaries to verify fail-closed setup."""

    settings = {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "NEMO_POLICY_SOURCE": "database", "NEMO_RUNTIME_CACHE_TTL_SECONDS": "300",
    }
    with patch.dict(os.environ, settings):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sqlalchemy import JSON, MetaData, create_engine
        from sqlalchemy.dialects.postgresql import JSONB
        from sqlalchemy.exc import SQLAlchemyError
        from sqlalchemy.orm import sessionmaker
        from nemo_mcp_guardrails.database import models, policy_loader, prompt_rule_loader
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database.policy_errors import PolicyLoadError
        from nemo_mcp_guardrails import runtime_factory as factory, tool_guard
        from nemo_mcp_guardrails.api import runtime
        from nemo_mcp_guardrails.api.auth import require_authenticated_app

        with patch.object(policy_loader, "SessionLocal") as database:
            importlib.reload(tool_guard)
            database.assert_not_called()
        with patch.object(policy_loader, "SessionLocal", side_effect=SQLAlchemyError("PRIVATE_DB_MARKER")):
            try:
                tool_guard.guard_mcp_tool(SimpleNamespace())
            except PolicyLoadError:
                pass
            else:
                raise AssertionError("Default tool wrapping bypassed the policy database")

        engine = create_engine("sqlite://")
        metadata = MetaData()
        for table in models.Base.metadata.sorted_tables:
            cloned = table.to_metadata(metadata)
            for column in cloned.columns:
                if isinstance(column.type, JSONB):
                    column.type = JSON()
                    column.server_default = None
        metadata.create_all(engine)
        sessions = sessionmaker(bind=engine)
        with sessions.begin() as db:
            global_input = models.PolicyRecord(policy_type="input", connector="github",
                                               action="create", resource="issue", conditions={})
            app_input = models.PolicyRecord(policy_type="input", connector="github",
                                            action="update", resource="file", conditions={})
            disabled_link = models.PolicyRecord(policy_type="input", connector="github",
                                                action="delete", resource="file", conditions={})
            output = models.PolicyRecord(policy_type="output", category="custom",
                                         conditions={"output_rule": "Do not disclose private material."})
            db.add_all([global_input, app_input, disabled_link, output])
            db.flush()
            global_id, app_id, output_id = global_input.id, app_input.id, output.id
            db.add_all([
                models.GlobalPolicyAssignmentRecord(policy_id=global_input.id),
                models.GlobalPolicyAssignmentRecord(policy_id=output.id),
                models.AppPolicyAssignmentRecord(app_id=1, policy_id=app_input.id),
                models.AppPolicyAssignmentRecord(app_id=2, policy_id=disabled_link.id, enabled=False),
            ])
            for record in (global_input, app_input, disabled_link, output):
                db.add(models.CompiledPolicyRuleRecord(
                    policy_id=record.id, rail_type=record.policy_type,
                    rule_text=f"Rule {record.id}",
                ))
            db.add(models.CompiledPolicyRuleRecord(
                policy_id=global_input.id, rail_type="input", rule_text="STALE",
                stale=True,
            ))
        with patch.object(policy_loader, "SessionLocal", sessions), patch.object(
            prompt_rule_loader, "SessionLocal", sessions,
        ):
            assert {(p.action, p.resource) for p in policy_loader.load_input_policy_objects(app_id=1)} == {
                ("create", "issue"), ("update", "file"),
            }
            assert {(p.action, p.resource) for p in policy_loader.load_input_policy_objects(app_id=2)} == {
                ("create", "issue"),
            }
            assert len(policy_loader.load_input_policy_objects()) == 3
            assert len(policy_loader.load_output_policy_objects(app_id=2)) == 1
            assert {r.policy_id for r in prompt_rule_loader.load_prompt_policy_rules(app_id=1)} == {
                global_id, app_id, output_id,
            }
            assert {r.policy_id for r in prompt_rule_loader.load_prompt_policy_rules(app_id=2)} == {
                global_id, output_id,
            }
            assert all(rule.rule_text != "STALE" for rule in prompt_rule_loader.load_prompt_policy_rules())

        loaders = (
            policy_loader.load_input_policy_entries,
            policy_loader.load_output_policy_objects,
            prompt_rule_loader.load_prompt_policy_rules,
        )
        for owner in (policy_loader, prompt_rule_loader):
            with patch.object(owner, "SessionLocal", side_effect=SQLAlchemyError("PRIVATE_DB_MARKER")):
                for loader in loaders:
                    if loader.__module__ != owner.__name__:
                        continue
                    for app_id in (None, 1):
                        try:
                            loader(app_id=app_id)
                        except PolicyLoadError:
                            pass
                        else:
                            raise AssertionError("Database failure returned fallback policies")
        with patch.object(policy_loader, "SessionLocal") as database, patch.object(
            prompt_rule_loader, "SessionLocal",
        ) as compiled:
            database.return_value.__enter__.return_value.scalars.return_value = []
            compiled.return_value.__enter__.return_value.scalars.return_value = []
            for loader in loaders:
                assert loader() == ()
                assert loader(app_id=1) == ()
        invalid = (
            (policy_loader._to_input_policy_object, models.PolicyRecord(conditions={})),
            (policy_loader._to_output_policy_object, models.PolicyRecord(category="custom", conditions=[])),
        )
        for convert, record in invalid:
            try:
                convert(record)
            except PolicyLoadError:
                pass
            else:
                raise AssertionError("Malformed policy was silently ignored")
        with patch.object(prompt_rule_loader, "SessionLocal") as database:
            database.return_value.__enter__.return_value.scalars.return_value = [
                SimpleNamespace(rail_type="output", rule_text=" "),
            ]
            try:
                prompt_rule_loader.load_prompt_policy_rules(app_id=1)
            except PolicyLoadError:
                pass
            else:
                raise AssertionError("Empty compiled policy was silently ignored")
        with patch.dict(os.environ, {"NEMO_POLICY_SOURCE": "defaults"}), patch.object(
            policy_loader, "SessionLocal",
        ) as database, patch.object(prompt_rule_loader, "SessionLocal") as compiled:
            assert policy_loader.load_input_policy_objects()
            assert policy_loader.load_output_policy_objects()
            assert {rule.rail_type for rule in prompt_rule_loader.load_prompt_policy_rules()} == {"input", "output"}
            database.assert_not_called()
            compiled.assert_not_called()
            try:
                asyncio.run(factory.build_guardrails_runtime_parts(1))
            except PolicyLoadError:
                pass
            else:
                raise AssertionError("Authenticated runtime accepted static policies")

        async def check_setup():
            """Prevent policy failures from starting models/tools or serving stale runtimes."""
            with ExitStack() as stack:
                stack.enter_context(patch.object(factory, "load_app_connector_config", return_value=object()))
                external = [stack.enter_context(patch.object(factory, name)) for name in (
                    "load_runtime_environment", "build_chat_model", "LLMRails", "create_agent",
                )]
                tools = stack.enter_context(patch.object(factory, "build_guarded_github_tools", AsyncMock()))
                for failing in (
                    "build_rails_config_with_prompt_rules", "compile_tool_guard_rules",
                    "load_runtime_policy_snapshot", "compile_blocked_output_phrases",
                ):
                    failure = (
                        ValueError("PRIVATE_COMPILER_MARKER")
                        if failing == "compile_tool_guard_rules"
                        else PolicyLoadError("PRIVATE_POLICY_MARKER")
                    )
                    with ExitStack() as attempt:
                        for name in (
                            "build_rails_config_with_prompt_rules", "compile_tool_guard_rules",
                            "load_runtime_policy_snapshot", "compile_blocked_output_phrases",
                        ):
                            attempt.enter_context(patch.object(factory, name,
                                **({"side_effect": failure}
                                   if name == failing else {"return_value": factory.RuntimePolicySnapshot(1, ()) if name == "load_runtime_policy_snapshot" else ()})))
                        try:
                            await factory._build_guardrails_runtime_parts_uncached(1)
                        except PolicyLoadError:
                            pass
                        else:
                            raise AssertionError("Incomplete policy configuration executed")
                for boundary in external:
                    boundary.assert_not_called()
                tools.assert_not_awaited()
            factory.clear_guardrails_runtime_cache()
            with patch.object(factory, "load_runtime_llm_selection", return_value=object()), patch.object(
                factory, "load_runtime_policy_snapshot", return_value=factory.RuntimePolicySnapshot(1, ()),
            ):
                await check_cache()

        async def check_cache():
            """Keep policy cache checks independent of the model grant store."""
            try:
                first, recovered = object(), object()
                with patch.object(factory, "load_runtime_revision", return_value=("old",)), patch.object(
                    factory, "_build_guardrails_runtime_parts_uncached", AsyncMock(return_value=first),
                ):
                    assert await factory.build_guardrails_runtime_parts(1) is first
                with patch.object(factory, "load_runtime_revision", side_effect=SQLAlchemyError("PRIVATE_DB_MARKER")):
                    try:
                        await factory.build_guardrails_runtime_parts(1)
                    except SQLAlchemyError:
                        pass
                    else:
                        raise AssertionError("Revision failure served a cached runtime")
                with patch.object(factory, "load_runtime_revision", return_value=("new",)), patch.object(
                    factory, "_build_guardrails_runtime_parts_uncached",
                    AsyncMock(side_effect=[PolicyLoadError("PRIVATE_POLICY_MARKER"), recovered]),
                ):
                    try:
                        await factory.build_guardrails_runtime_parts(1)
                    except PolicyLoadError:
                        pass
                    else:
                        raise AssertionError("Failed refresh returned an older runtime")
                    assert factory._RUNTIME_PARTS_CACHE[1].parts is first
                    assert await factory.build_guardrails_runtime_parts(1) is recovered
            finally:
                factory.clear_guardrails_runtime_cache()

        asyncio.run(check_setup())
        app = FastAPI()
        app.include_router(runtime.router)
        app.dependency_overrides[require_authenticated_app] = lambda: SimpleNamespace(id=1, client_id="policy-test")
        app.dependency_overrides[get_db] = lambda: None
        with TestClient(app) as client:
            for error in (PolicyLoadError("PRIVATE_POLICY_MARKER"), SQLAlchemyError("PRIVATE_DB_MARKER")):
                with patch.object(runtime, "build_guardrails_runtime_parts", AsyncMock(side_effect=error)), patch.object(
                    runtime, "execute_guarded_message", AsyncMock(),
                ) as execute:
                    response = client.post("/v1/guardrails/run", json={"message": "Review."})
                assert response.status_code == 503, response.text
                assert response.json() == {"detail": (
                    "Runtime policies are unavailable. Ask a GMS administrator to review the policy configuration."
                )}
                assert "PRIVATE_" not in response.text
                execute.assert_not_awaited()
        engine.dispose()
        print("Policy fail-closed checks passed (scope, errors, defaults, setup, cache, and HTTP).")


if __name__ == "__main__":
    main()
