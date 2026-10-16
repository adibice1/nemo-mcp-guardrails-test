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
            {"value": "review", "label": "Review", "resources": [{"value": "pull_request", "label": "Pull Request"}]},
        ])]
        draft = {
            "policy_type": "input", "name": "Block PR 17 merges", "connector": "github", "action": "merge",
            "resource": "pull_request",
            "custom_resource": "number = 17",
            "explanation": "Restrict merging pull request number 17.",
            "examples": [{"prompt": "Merge pull request number 17", "expected": "block"}],
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
        payload = {"prompt": "Block merging pull request number 17"}
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
            instructions = provider.chat.completions.create.call_args.kwargs["messages"][0]["content"]
            assert "two distinct fields joined by AND" in instructions
            assert "never remove a condition" in instructions
            assert '"fields": ["number", "source_branch", "target_branch"]' in instructions

            related = {**draft, "action": "review", "name": "Block PR 17 reviews"}
            provider.chat.completions.create.return_value = completion({**valid, "related": [related]})
            assert client.post("/policy-assistant/suggest", json=payload, headers=headers).json() == {
                **valid, "related": [related],
            }
            for selector, canonical in (
                ('title = "Release Ready!"', 'title = "release ready!"'),
                ('target_branch = "Production"', 'target_branch = "Production"'),
                ('source_branch = "Feature/Auth"', 'source_branch = "Feature/Auth"'),
                ('target_branch = "production" AND source_branch != "staging"',
                 'source_branch != "staging" AND target_branch = "production"'),
                ('title = ' + json.dumps('Caf\u00e9 "Ready"', ensure_ascii=False),
                 'title = ' + json.dumps('caf\u00e9 "ready"', ensure_ascii=False)),
                ("", ""),
            ):
                title_draft = {**draft, "action": "create", "custom_resource": selector}
                provider.chat.completions.create.return_value = completion({**valid, "draft": title_draft})
                request = {"prompt": "Block creating pull requests " + ("where " + selector if selector else "in all cases")}
                response = client.post("/policy-assistant/suggest", json=request, headers=headers)
                assert response.status_code == 200, response.text
                assert response.json()["draft"]["custom_resource"] == canonical

            route = 'source_branch != "staging" AND target_branch = "production"'
            provider.chat.completions.create.return_value = completion({**valid, "draft": {**draft, "custom_resource": route}})
            merge_response = client.post("/policy-assistant/suggest", json=payload, headers=headers)
            assert merge_response.status_code == 200
            assert "Selective merging is unavailable" in merge_response.json()["draft"]["explanation"]

            for selector in (
                "whose target is production and whose source is not staging",
                'target_branch = "production" OR source_branch = "staging"',
                "number = 0",
                'number = "17"',
                "A -> B -> C",
                'number = 17 OR number = 18',
            ):
                unsupported = {**draft, "custom_resource": selector}
                for result in ({**valid, "draft": unsupported}, {**valid, "related": [unsupported]}):
                    provider.chat.completions.create.return_value = completion(result)
                    response = client.post("/policy-assistant/suggest", json=payload, headers=headers)
                    assert response.status_code == 200, response.text
                    assert response.headers["cache-control"] == "no-store"
                    assert response.json()["draft"] is None and response.json()["related"] == []
                    assert "unsupported resource condition" in response.json()["clarification"]
                    assert selector not in response.json()["clarification"]

            for selector in ("", "number = 18"):
                provider.chat.completions.create.return_value = completion({
                    **valid, "related": [{**related, "custom_resource": selector}],
                })
                response = client.post("/policy-assistant/suggest", json=payload, headers=headers)
                assert response.status_code == 200, response.text
                assert response.json()["draft"] is None and response.json()["related"] == []
                assert "related-policy scope" in response.json()["clarification"]

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

            clarification = {"draft": None, "related": [], "clarification": "Which pull request number?"}
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
    print("Policy assistant offline checks passed: JWT, canonical input/related drafts, unsupported conditions, output isolation, clarification and provider failures.")


if __name__ == "__main__":
    main()
