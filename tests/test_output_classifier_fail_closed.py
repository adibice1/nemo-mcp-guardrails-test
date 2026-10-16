"""Offline regressions for failed Azure output classifications."""

import asyncio
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Exercise execution, HTTP serialization, history, and metadata offline."""

    settings = {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "NEMO_POLICY_SOURCE": "defaults",
    }
    with patch.dict(os.environ, settings):
        import httpx
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from langchain_core.messages import AIMessage
        from nemoguardrails.exceptions import LLMCallException
        from nemoguardrails.rails.llm.options import RailStatus
        from openai import BadRequestError
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        import nemo_mcp_guardrails.api.runtime as runtime
        import nemo_mcp_guardrails.guarded_execution as execution
        import nemo_mcp_guardrails.runtime_logging as logging
        from nemo_mcp_guardrails.api.auth import require_authenticated_app
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database.models import ConversationMessageRecord

        def filter_error(kind):
            """Represent both structured provider errors and LangChain filtering."""
            if kind == "value":
                return ValueError(execution.AZURE_FILTERED_RESPONSE_MESSAGE)
            error = BadRequestError(
                "PRIVATE_ERROR_MARKER",
                response=httpx.Response(400, request=httpx.Request("POST", "https://example.invalid")),
                body={"error": {"code": "content_filter", "innererror": {
                    "content_filter_result": {
                        "hate": {"filtered": True},
                        "violence": {"filtered": False},
                    }
                }}},
            )
            return LLMCallException(error) if kind == "wrapped" else error

        engine = create_engine(
            "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False},
        )
        ConversationMessageRecord.__table__.create(engine)
        sessions = sessionmaker(bind=engine)

        def test_db():
            """Supply isolated conversation persistence without external services."""
            with sessions() as db:
                yield db

        app = FastAPI()
        app.include_router(runtime.router)
        app.add_middleware(logging.RuntimeLogMiddleware)
        app.dependency_overrides[get_db] = test_db
        def authenticated_app(request: Request):
            """Supply an authenticated identity and its normal logging context."""
            request.state.gms_runtime_app_id = 1
            return SimpleNamespace(id=1, client_id="output-classification-test")

        app.dependency_overrides[require_authenticated_app] = authenticated_app
        outputs = ("PRIVATE_UNCLASSIFIED_MARKER", "API_KEY=PRIVATE_UNCLASSIFIED_MARKER")
        count = 0
        with TestClient(app) as client:
            for debug in ("0", "1"):
                for kind in ("wrapped", "raw", "value"):
                    for output in outputs:
                        count += 1
                        rails = SimpleNamespace(check_async=AsyncMock(side_effect=[
                            SimpleNamespace(status=RailStatus.PASSED, content=""),
                            filter_error(kind),
                        ]))
                        agent = SimpleNamespace(ainvoke=AsyncMock(return_value={
                            "messages": [AIMessage(content=output)],
                        }))
                        parts = SimpleNamespace(
                            rails=rails, agent=agent, output_rail_enabled=True,
                            blocked_output_phrases=(), input_policy_count=0,
                            input_policy_entries=(), blocked_tools=frozenset(),
                            prompt_rule_config=SimpleNamespace(
                                input_rule_count=0, output_rule_count=1, prompt_rules=(),
                            ),
                        )
                        with patch.dict(os.environ, {"NEMO_RUNTIME_DEBUG": debug}), patch.object(
                            runtime, "build_guardrails_runtime_parts", AsyncMock(return_value=parts),
                        ), patch.object(logging, "_persist_runtime_log") as persisted:
                            response = client.post("/v1/guardrails/run", json={
                                "message": "Review this request.",
                                "conversation_id": f"filtered-{count}",
                            })
                        assert response.status_code == 200, response.text
                        body = response.json()
                        assert body["status"] == "blocked", body
                        assert body["input_rail_status"] == "passed"
                        assert body["output_rail_status"] == "blocked"
                        assert body["output_rail_source"] == "azure_content_filter"
                        assert body["output_rail_categories"] == ([] if kind == "value" else ["hate"])
                        assert body["block_stage"] == "output"
                        assert body["response"] == body["block_reason"]
                        assert "Azure content filter" in body["response"]
                        assert body["debug_agent_response"] is None
                        assert body["debug_output_rule_texts"] is None
                        assert body["debug_output_rail_source"] == (
                            "azure_content_filter" if debug == "1" else None
                        )
                        assert "PRIVATE_" not in response.text
                        rails.check_async.assert_awaited()
                        assert rails.check_async.await_count == 2
                        agent.ainvoke.assert_awaited_once()
                        with sessions() as db:
                            turns = list(db.scalars(select(ConversationMessageRecord).where(
                                ConversationMessageRecord.conversation_id == f"filtered-{count}",
                            ).order_by(ConversationMessageRecord.id)))
                            assert [(turn.role, turn.content) for turn in turns] == [
                                ("user", "Review this request."), ("assistant", body["response"]),
                            ]
                        persisted.assert_called_once()
                        log, events, user_log = persisted.call_args.args
                        assert log["outcome"] == "blocked"
                        assert user_log["response_text"] == body["response"]
                        assert "PRIVATE_" not in repr(user_log)
                        output_events = [event for event in events if
                                         event["stage"] == "output" and event["event"] == "rail.completed"]
                        assert len(output_events) == 1
                        assert output_events[0]["outcome"] == "blocked"
                        assert output_events[0]["reason_code"] == "azure_content_filter"
                        assert "PRIVATE_" not in repr(events)

        async def check_other_outcomes():
            """Preserve normal classifications and unrelated provider failures."""
            for status in (RailStatus.PASSED, RailStatus.BLOCKED, RailStatus.MODIFIED):
                rails = SimpleNamespace(check_async=AsyncMock(return_value=SimpleNamespace(
                    status=status, content="Modified response.",
                )))
                response, result = await execution.apply_output_rail(rails, "Review.", "Original.")
                assert result.status == status
                assert response == {
                    RailStatus.PASSED: "Original.",
                    RailStatus.BLOCKED: execution.TOOL_GUARD_REFUSAL,
                    RailStatus.MODIFIED: "Modified response.",
                }[status]
            bad_request = BadRequestError(
                "Not a content-filter error",
                response=httpx.Response(400, request=httpx.Request("POST", "https://example.invalid")),
                body={"error": {"code": "invalid_request"}},
            )
            for error in (
                bad_request, LLMCallException(bad_request),
                ValueError("Unexpected parsing failure"), TimeoutError("Timeout"),
            ):
                rails = SimpleNamespace(check_async=AsyncMock(side_effect=error))
                try:
                    await execution.apply_output_rail(rails, "Review.", "Original.")
                except Exception as observed:
                    assert observed is error
                else:
                    raise AssertionError("Unrelated failure was suppressed")

        asyncio.run(check_other_outcomes())
        engine.dispose()
        print("Output classification checks passed (12 HTTP/history/log cases; normal/error controls).")


if __name__ == "__main__":
    main()
