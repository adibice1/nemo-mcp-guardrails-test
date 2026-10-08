"""Offline checks for authenticated, bounded, non-persistent AI drafts."""

import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Test real JWT protection and provider failures using isolated SQLite."""
    settings = {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "GMS_JWT_SECRET": "policy-assistant-test-secret-at-least-32-chars",
        "AZURE_OPENAI_API_KEY": "test-key", "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
        "AZURE_OPENAI_API_VERSION": "2024-12-01-preview", "AZURE_OPENAI_DEPLOYMENT": "test-deployment",
    }
    with patch.dict(os.environ, settings):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine, func, select
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        import nemo_mcp_guardrails.api.policy_assistant as module
        from nemo_mcp_guardrails.api.policy_schemas import PolicyConnectorOption
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database.models import UserRecord
        from nemo_mcp_guardrails.management_auth import create_access_token

        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        UserRecord.__table__.create(engine)
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        with sessions.begin() as db:
            user = UserRecord(email="developer@example.com", name="Test Developer",
                              username="test-developer", password_hash="unused",
                              system_role="developer", enabled=True)
            db.add(user)
            db.flush()
            token = create_access_token(user)

        def test_db():
            """Provide disposable sessions for real authentication."""
            with sessions() as db:
                yield db

        app = FastAPI()
        app.include_router(module.router)
        app.dependency_overrides[get_db] = test_db
        options = [PolicyConnectorOption(value="github", label="GitHub", actions=[
            {"value": "merge", "label": "Merge", "resources": [{"value": "pull_request", "label": "Pull Request"}]},
            {"value": "create", "label": "Create", "resources": [{"value": "pull_request", "label": "Pull Request"}]},
        ])]
        draft = {
            "policy_type": "input", "name": "Block unsafe production merges", "connector": "github", "action": "merge",
            "resource": "pull_request",
            "custom_resource": "whose target is production and whose source is not staging",
            "explanation": "Restrict production merges from non-staging branches.",
            "examples": [{"prompt": "Merge feature into production", "expected": "block"}],
        }
        valid = {"draft": draft, "related": [], "clarification": ""}

        def completion(payload, finish_reason="stop", refusal=None):
            """Return the same envelope as a provider chat completion."""
            return SimpleNamespace(choices=[SimpleNamespace(
                finish_reason=finish_reason,
                message=SimpleNamespace(content=json.dumps(payload), refusal=refusal),
            )])

        provider = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
            create=AsyncMock(return_value=completion(valid)))))
        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=provider)
        context.__aexit__ = AsyncMock(return_value=None)
        headers = {"Authorization": "Bearer " + token}
        payload = {"prompt": "Prevent non-staging merges into production"}
        with patch.object(module, "list_policy_options", return_value=options), \
             patch.object(module, "AsyncAzureOpenAI", return_value=context), TestClient(app) as client:
            assert client.post("/policy-assistant/suggest", json=payload).status_code == 401
            assert client.post("/policy-assistant/suggest", json=payload,
                               headers={"Authorization": "Bearer invalid"}).status_code == 401
            assert provider.chat.completions.create.await_count == 0
            response = client.post("/policy-assistant/suggest", json=payload, headers=headers)
            assert response.status_code == 200, response.text
            assert response.json() == valid
            assert response.headers["cache-control"] == "no-store"

            before = provider.chat.completions.create.await_count
            for invalid in ({"prompt": " "}, {"prompt": "x" * 2001}, {**payload, "global": True}):
                assert client.post("/policy-assistant/suggest", json=invalid, headers=headers).status_code == 422
            assert provider.chat.completions.create.await_count == before

            for bad in (
                {**valid, "draft": {**draft, "resource": "issue"}},
                {**valid, "related": [{**draft, "action": "delete"}]},
                {**valid, "draft": {**draft, "global": True}},
            ):
                provider.chat.completions.create.return_value = completion(bad)
                response = client.post("/policy-assistant/suggest", json=payload, headers=headers)
                assert response.status_code == 502
                assert "test-key" not in response.text

            clarification = {"draft": None, "related": [], "clarification": "Which source and target branches?"}
            provider.chat.completions.create.return_value = completion(clarification)
            assert client.post("/policy-assistant/suggest", json=payload, headers=headers).json() == clarification

            for finish, refusal, expected in (("length", None, 502), ("stop", "refused", 422)):
                provider.chat.completions.create.return_value = completion(valid, finish, refusal)
                assert client.post("/policy-assistant/suggest", json=payload, headers=headers).status_code == expected

            provider.chat.completions.create.side_effect = TimeoutError()
            assert client.post("/policy-assistant/suggest", json=payload, headers=headers).status_code == 504
            provider.chat.completions.create.side_effect = None
            with patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": ""}):
                assert client.post("/policy-assistant/suggest", json=payload, headers=headers).status_code == 503
            with patch.object(module, "list_policy_options", return_value=[]):
                assert client.post("/policy-assistant/suggest", json=payload, headers=headers).status_code == 503

        output_payload = {"policy_type": "output", "prompt": 'Block responses containing the word "hello"'}
        output_draft = {
            "policy_type": "output", "name": "Block hello in responses",
            "output_rule": 'Do not include the word "hello" in assistant responses.',
            "explanation": "Check assistant responses, not user prompts.",
            "examples": [
                {"prompt": "Hello!", "expected": "block"},
                {"prompt": "Good morning.", "expected": "not_blocked_by_this_policy"},
                {"prompt": "shelloworld", "expected": "not_blocked_by_this_policy"},
            ],
        }
        output_valid = {"draft": output_draft, "related": [], "clarification": ""}
        provider.chat.completions.create.return_value = completion(output_valid)
        with patch.object(module, "list_policy_options", side_effect=AssertionError("Output must not read GitHub metadata")), \
             patch.object(module, "AsyncAzureOpenAI", return_value=context), TestClient(app) as client:
            before = provider.chat.completions.create.await_count
            assert client.post("/policy-assistant/suggest", json=output_payload).status_code == 401
            assert client.post("/policy-assistant/suggest", json={**output_payload, "policy_type": "tool"},
                               headers=headers).status_code == 422
            assert provider.chat.completions.create.await_count == before
            response = client.post("/policy-assistant/suggest", json=output_payload, headers=headers)
            assert response.status_code == 200, response.text
            assert response.json() == output_valid
            assert response.headers["cache-control"] == "no-store"
            for bad in (
                valid,
                {**output_valid, "related": [draft]},
                {**output_valid, "related": [output_draft]},
                {**output_valid, "draft": {**output_draft, "output_rule": " "}},
                {**output_valid, "draft": {**output_draft, "connector": "github"}},
            ):
                provider.chat.completions.create.return_value = completion(bad)
                assert client.post("/policy-assistant/suggest", json=output_payload, headers=headers).status_code == 502
            provider.chat.completions.create.return_value = completion(clarification)
            assert client.post("/policy-assistant/suggest", json=output_payload, headers=headers).json() == clarification

        from nemo_mcp_guardrails.output_guard import compile_blocked_output_phrases, find_blocked_output_phrase

        phrases = compile_blocked_output_phrases([output_draft["output_rule"]])
        assert phrases == ("hello",)
        assert find_blocked_output_phrase("Hello!", phrases) == "hello"
        assert find_blocked_output_phrase("Good morning.", phrases) is None
        assert find_blocked_output_phrase("shelloworld", phrases) is None

        with sessions() as db:
            assert db.scalar(select(func.count(UserRecord.id))) == 1
        engine.dispose()
    print("Policy assistant offline checks passed: JWT, input/output drafts, rail validation, output word matching, metadata, clarification, refusal, timeout, and configuration errors.")


if __name__ == "__main__":
    main()
