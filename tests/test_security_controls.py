"""Disposable-data regressions for throttling, setup passwords and bounded requests."""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from _bootstrap import bootstrap_src
bootstrap_src()


def main() -> None:
    """Exercise actual HTTP and SQL boundaries without external services."""
    with patch.dict(os.environ, {
        "PYTHON_DOTENV_DISABLED": "1", "DATABASE_URL": "sqlite://",
        "GMS_JWT_SECRET": "security-controls-test-secret-at-least-32-characters",
    }):
        from fastapi import Depends, FastAPI, HTTPException
        from fastapi.testclient import TestClient
        from fastapi.exceptions import RequestValidationError
        from pydantic import ValidationError
        from sqlalchemy import JSON, MetaData, create_engine, func, select, text
        from sqlalchemy.dialects.postgresql import JSONB
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from nemo_mcp_guardrails.api import management_auth as auth, management_users as users
        from nemo_mcp_guardrails.api.runtime_schemas import GuardrailsRunRequest
        from nemo_mcp_guardrails.database import models
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database.conversation_store import load_conversation_turns
        from nemo_mcp_guardrails.management_auth import create_access_token, hash_password, verify_password
        from nemo_mcp_guardrails.rate_limits import RateLimiter
        from nemo_mcp_guardrails.request_limits import RequestBodyLimitMiddleware, validation_error_response
        from backfill_existing_app_users import backfill_link
        from migrate_security_foundation import migrate

        clock = [0.0]
        limiter = RateLimiter(capacity=2, clock=lambda: clock[0])
        limiter.check("private-a", 2, 10)
        limiter.check("private-a", 2, 10)
        for key in ("private-a", "third"):
            if key == "third":
                limiter.check("private-b", 1, 10)
            try:
                limiter.check(key, 2, 10)
                raise AssertionError("Limit did not reject")
            except HTTPException as error:
                assert error.status_code == 429 and int(error.headers["Retry-After"]) > 0
        assert len(limiter.buckets) == 2 and all(isinstance(k, bytes) for k in limiter.buckets)
        clock[0] = 10
        limiter.check("third", 1, 10)
        assert len(limiter.buckets) == 1

        engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        metadata = MetaData()
        for table in models.Base.metadata.sorted_tables:
            clone = table.to_metadata(metadata)
            for column in clone.columns:
                if isinstance(column.type, JSONB):
                    column.type = JSON()
                    column.server_default = None
        metadata.create_all(engine)
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        with sessions.begin() as db:
            admin = models.UserRecord(email="admin@example.invalid", username="admin", name="Admin",
                password_hash=hash_password("existing personal passphrase"), system_role="admin", enabled=True)
            db.add(admin)
            db.add_all([models.AppRecord(id=i, name=f"App {i}", client_id=f"app-{i}", api_key_hash="unused") for i in (1, 2)])
            db.flush()
            admin_headers = {"Authorization": "Bearer " + create_access_token(admin)}
            admin_id = admin.id

        def test_db():
            """Supply independent disposable sessions to authentication and handlers."""
            with sessions() as db:
                yield db

        app = FastAPI()
        app.add_exception_handler(RequestValidationError, validation_error_response)
        app.include_router(auth.router)
        app.include_router(users.router)
        app.dependency_overrides[get_db] = test_db

        @app.get("/protected")
        def protected(user=Depends(auth.require_management_user)):
            """Prove the common dependency protects every management surface."""
            return {"id": user.id}

        with TestClient(app) as client:
            response = client.post("/management-users", headers=admin_headers, json={"email": "new@example.invalid"})
            assert response.status_code == 201, response.text
            created = response.json()
            temporary = created["temporary_password"]
            assert created["must_change_password"] and created["temporary_password_expires_at"]

            def login(password):
                """Use the real password verifier and setup/normal token issuance."""
                response = client.post("/management-auth/login", json={"email": created["email"], "password": password})
                assert response.status_code == 200, response.text
                return {"Authorization": "Bearer " + response.json()["access_token"]}

            setup = login(temporary)
            malformed = client.put("/management-auth/me/password", headers={**setup, "Content-Type": "application/json"},
                content='{"current_password":"fake","new_password":"' + '\\ud800' + 'x' * 20 + '"}')
            assert malformed.status_code == 422 and malformed.json() == {"detail": "Request contains invalid fields."}
            assert not verify_password("wrong", "scrypt$YQ==$YQ==")
            assert client.get("/management-auth/me", headers=setup).json()["must_change_password"]
            assert client.get("/protected", headers=setup).status_code == 403
            assert client.get("/management-users", headers=setup).status_code == 403
            assert client.put("/management-auth/me", headers=setup, json={"name": "New", "username": "new"}).status_code == 403
            response = client.put("/management-auth/me/password", headers=setup, json={
                "current_password": temporary, "new_password": "new personal passphrase",
            })
            assert response.status_code == 204, response.text
            assert client.get("/protected", headers=setup).status_code == 401
            normal = login("new personal passphrase")
            assert client.get("/protected", headers=normal).status_code == 200
            reset = client.post(f"/management-users/{created['id']}/password", headers=admin_headers)
            assert reset.status_code == 200, reset.text
            assert client.get("/protected", headers=normal).status_code == 401
            with sessions.begin() as db:
                db.get(models.UserRecord, created["id"]).temporary_password_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            expired = client.post("/management-auth/login", json={"email": created["email"], "password": reset.json()["temporary_password"]})
            assert expired.status_code == 401 and expired.json()["detail"] == auth.INVALID_CREDENTIALS

            with patch("nemo_mcp_guardrails.rate_limits.limiter", RateLimiter(clock=lambda: clock[0])), \
                 patch.object(auth, "verify_password", wraps=auth.verify_password) as verify:
                for i in range(10):
                    assert client.post("/management-auth/login", json={"email": "unknown@example.invalid", "password": "wrong"},
                        headers={"X-Forwarded-For": f"spoof-{i}"}).status_code == 401
                assert verify.call_count == 10
                limited = client.post("/management-auth/login", json={"email": "unknown@example.invalid", "password": "wrong"})
                assert limited.status_code == 429 and verify.call_count == 10

        with sessions.begin() as db:
            assert backfill_link(db, admin_id, 1)
            assert db.scalar(select(func.count(models.AppUserRecord.id))) == 0
            assert backfill_link(db, admin_id, 1, apply=True)
            assert not backfill_link(db, admin_id, 1, apply=True)
            assert db.scalar(select(func.count(models.AppUserRecord.id))) == 1
            for i in range(40):
                db.add(models.ConversationMessageRecord(app_id=1, conversation_id="same", role="user", content=str(i)))
            db.add(models.ConversationMessageRecord(app_id=2, conversation_id="same", role="user", content="other-app"))
            db.flush()
            turns = load_conversation_turns(db, 1, "same")
            assert len(turns) == 33 and [t.content for t in turns] == [str(i) for i in range(7, 40)]
            plan = db.execute(text("EXPLAIN QUERY PLAN SELECT id FROM conversation_messages WHERE app_id=1 AND conversation_id='same' ORDER BY id DESC LIMIT 33")).all()
            assert "ix_conversation_messages_scope_tail" in str(plan)
            from nemo_mcp_guardrails.api.runtime import _build_runtime_history_context
            context = _build_runtime_history_context(GuardrailsRunRequest(message="next", conversation_id="same"), 1, db)
            assert context.truncated and context.loaded_count == 33
            db.add(models.ConversationMessageRecord(app_id=1, conversation_id="same", role="assistant", content="x" * 50000))
            db.flush()
            bounded = load_conversation_turns(db, 1, "same")
            assert len(bounded[-1].content) == 16001
            context = _build_runtime_history_context(GuardrailsRunRequest(message="next", conversation_id="same"), 1, db)
            assert context.truncated and context.selected_turns == ()

        for payload in ({"message": "x" * 16001}, {"message": "bad\x00text"}, {"message": "ok", "conversation_id": "bad\ntext"}, {"message": "ok", "conversation_id": " "},
                        {"message": "ok", "conversation_history": [{"role": "user", "content": "x"}] * 33},
                        {"message": "ok", "conversation_history": [{"role": "user", "content": "x" * 16000}] * 5}):
            try:
                GuardrailsRunRequest(**payload)
                raise AssertionError("Oversized request accepted")
            except ValidationError:
                pass

        async def check_body():
            """Prove exact byte caps for chunked and dishonest-length bodies."""
            invoked = []
            async def inner(scope, receive, send):
                invoked.append((await receive())["body"])
            for parts, accepted in (([b"1234", b"5678"], True), ([b"1234", b"56789"], False)):
                incoming = iter({"type": "http.request", "body": part, "more_body": i < len(parts) - 1} for i, part in enumerate(parts))
                sent = []
                async def receive():
                    return next(incoming)
                async def send(message):
                    sent.append(message)
                before = len(invoked)
                await RequestBodyLimitMiddleware(inner, max_bytes=8)({"type": "http", "headers": [(b"content-length", b"1")]}, receive, send)
                assert (len(invoked) > before) == accepted
                if not accepted:
                    assert sent[0]["status"] == 413
        asyncio.run(check_body())

        legacy = create_engine("sqlite://")
        with legacy.begin() as connection:
            connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, password_hash TEXT)"))
            connection.execute(text("INSERT INTO users VALUES (1, 'unchanged')"))
            connection.execute(text("CREATE TABLE conversation_messages (id INTEGER, app_id INTEGER, conversation_id TEXT)"))
            migrate(connection)
            migrate(connection)
            assert connection.execute(text("SELECT password_hash, must_change_password, temporary_password_expires_at FROM users")).one() == ("unchanged", 0, None)
        engine.dispose()
        legacy.dispose()
    print("Security controls passed: bounded throttling, setup/expiry/reset/session revocation, byte/schema/history bounds, scoped index, safe backfill and idempotent schema.")


if __name__ == "__main__":
    main()
