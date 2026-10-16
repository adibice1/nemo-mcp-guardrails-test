"""Offline HTTP regressions for runtime debug-content privacy."""

import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Check debug privacy for passed, blocked, and modified output offline."""

    settings = {
        "PYTHON_DOTENV_DISABLED": "1",
        "DATABASE_URL": "sqlite://",
        "NEMO_POLICY_SOURCE": "defaults",
    }
    with patch.dict(os.environ, settings):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from langchain_core.messages import AIMessage, ToolMessage
        from nemoguardrails.rails.llm.options import RailStatus
        import nemo_mcp_guardrails.api.runtime as module
        from nemo_mcp_guardrails.api.auth import require_authenticated_app
        from nemo_mcp_guardrails.database.connection import get_db

        app = FastAPI()
        app.include_router(module.router)
        app.dependency_overrides[require_authenticated_app] = lambda: SimpleNamespace(
            id=1, client_id="debug-privacy-test"
        )

        def no_database():
            """Provide no database; requests have no persistent conversation."""
            yield None

        app.dependency_overrides[get_db] = no_database
        messages = [
            AIMessage(content="", tool_calls=[{
                "name": "review_tool", "id": "review-call",
                "args": {"path": "PRIVATE_ARGUMENT_MARKER"},
            }]),
            ToolMessage(content="PRIVATE_TOOL_RESULT_MARKER",
                        tool_call_id="review-call", name="review_tool"),
            AIMessage(content="PRIVATE_AGENT_MARKER"),
        ]
        rules = (SimpleNamespace(rail_type="output",
                                 rule_text="PRIVATE_POLICY_MARKER"),)

        with TestClient(app) as client:
            for debug in ("0", "1"):
                for output_status in (
                    RailStatus.PASSED, RailStatus.BLOCKED, RailStatus.MODIFIED
                ):
                    rails = SimpleNamespace(check_async=AsyncMock(side_effect=[
                        SimpleNamespace(status=RailStatus.PASSED, content=""),
                        SimpleNamespace(status=output_status, content="Filtered response."),
                    ]))
                    parts = SimpleNamespace(
                        rails=rails,
                        agent=SimpleNamespace(ainvoke=AsyncMock(
                            return_value={"messages": messages})),
                        output_rail_enabled=True, blocked_output_phrases=(),
                        input_policy_count=0, input_policy_entries=(),
                        blocked_tools=frozenset(),
                        prompt_rule_config=SimpleNamespace(
                            input_rule_count=0, output_rule_count=1,
                            prompt_rules=rules),
                    )
                    with patch.dict(os.environ, {"NEMO_RUNTIME_DEBUG": debug}), patch.object(
                        module, "build_guardrails_runtime_parts",
                        AsyncMock(return_value=parts),
                    ):
                        response = client.post("/v1/guardrails/run",
                                               json={"message": "Review this request."})
                    assert response.status_code == 200, response.status_code
                    body = response.json()
                    assert body["debug_agent_response"] is None
                    assert body["debug_output_rule_texts"] is None
                    for marker in ("PRIVATE_ARGUMENT_MARKER", "PRIVATE_TOOL_RESULT_MARKER",
                                   "PRIVATE_POLICY_MARKER"):
                        assert marker not in response.text, marker
                    if output_status != RailStatus.PASSED:
                        assert "PRIVATE_AGENT_MARKER" not in response.text
                    assert body["status"] == (
                        "blocked" if output_status == RailStatus.BLOCKED else "passed"
                    )
                    if output_status == RailStatus.MODIFIED:
                        assert body["response"] == "Filtered response."
                    elif output_status == RailStatus.PASSED:
                        assert body["response"] == "PRIVATE_AGENT_MARKER"
                    if debug == "1":
                        assert body["debug_output_rail_source"] is not None
                        assert body["debug_tool_trace"] == [
                            {"event": "call", "tool_name": "review_tool"},
                            {"event": "result", "tool_name": "review_tool"},
                        ]
                    else:
                        assert body["debug_tool_trace"] is None
                        assert body["debug_output_rail_source"] is None

        print("Runtime debug privacy checks passed (six HTTP cases).")


if __name__ == "__main__":
    main()
