"""Explicit opt-in HTTP/PostgreSQL smoke test for an empty disposable review DB."""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.request import Request as HttpRequest, urlopen


def main() -> None:
    """Refuse ordinary environments before exercising the disposable deployment."""
    if os.getenv("GMS_DISPOSABLE_TEST_DB") != "1" or os.getenv("PYTHON_DOTENV_DISABLED") != "1":
        raise RuntimeError("This check requires an explicitly disposable, dotenv-disabled test container.")
    from sqlalchemy import func, select, text
    from sqlalchemy.engine import make_url
    url = make_url(os.environ["DATABASE_URL"])
    if url.host != "reviewdb" or url.database != "review":
        raise RuntimeError("Only the isolated reviewdb/review test database is accepted.")
    from _bootstrap import bootstrap_src
    bootstrap_src()
    from fastapi import HTTPException
    from starlette.requests import Request
    from nemo_mcp_guardrails.api.management_auth import change_current_password
    from nemo_mcp_guardrails.api.management_auth_schemas import ManagementPasswordChange
    from nemo_mcp_guardrails.database.connection import SessionLocal, engine
    from nemo_mcp_guardrails.database.models import UserRecord
    from nemo_mcp_guardrails.management_auth import hash_password
    from migrate_security_foundation import migrate

    def request(method, path, payload=None, token=None):
        """Call only the backend's loopback HTTP listener with synthetic data."""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        data = json.dumps(payload).encode() if payload is not None else None
        try:
            response = urlopen(HttpRequest("http://127.0.0.1:8000" + path, data=data, method=method, headers=headers), timeout=5)
        except HTTPError as error:
            response = error
        with response:
            body = response.read()
            return response.status, json.loads(body) if body else None, response.headers

    for attempt in range(50):
        try:
            if request("GET", "/health")[0] == 200:
                break
        except OSError:
            if attempt == 49:
                raise
            time.sleep(0.2)
    with SessionLocal.begin() as db:
        if db.scalar(select(func.count(UserRecord.id))):
            raise RuntimeError("Refusing to seed a database that already contains users.")
        db.add(UserRecord(email="admin@example.invalid", name="Admin", username="admin", system_role="admin",
                          enabled=True, password_hash=hash_password("review administrator passphrase")))
    status, login, _ = request("POST", "/management-auth/login", {
        "email": "admin@example.invalid", "password": "review administrator passphrase",
    })
    assert status == 200
    admin_token = login["access_token"]
    status, created, headers = request("POST", "/management-users", {"email": "new@example.invalid"}, admin_token)
    assert status == 201 and created["must_change_password"] and headers["Cache-Control"] == "no-store"
    temporary = created["temporary_password"]
    status, login, _ = request("POST", "/management-auth/login", {"email": created["email"], "password": temporary})
    assert status == 200
    setup_token = login["access_token"]
    assert request("GET", "/apps", token=setup_token)[0] == 403
    assert request("GET", "/management-auth/me", token=setup_token)[1]["must_change_password"]
    assert request("PUT", "/management-auth/me/password", {
        "current_password": temporary, "new_password": "review personal passphrase",
    }, setup_token)[0] == 204
    assert request("GET", "/management-auth/me", token=setup_token)[0] == 401
    status, login, _ = request("POST", "/management-auth/login", {
        "email": created["email"], "password": "review personal passphrase",
    })
    assert status == 200 and not login["user"]["must_change_password"]
    assert request("GET", "/apps", token=login["access_token"])[0] == 200
    assert request("POST", "/v1/guardrails/run", {"message": "synthetic test"})[0] == 401
    # A committed administrator reset wins over a stale password-change transaction.
    with SessionLocal.begin() as other:
        changed = other.get(UserRecord, created["id"])
        changed.password_hash = hash_password("competing administrator reset")
        changed.must_change_password = True
        changed.temporary_password_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    # Reload a deliberately stale snapshot in an independent transaction.
    with SessionLocal() as stale:
        snapshot = stale.get(UserRecord, created["id"])
        with SessionLocal.begin() as other:
            other.get(UserRecord, created["id"]).password_hash = hash_password("second competing reset")
        try:
            change_current_password(ManagementPasswordChange(current_password="competing administrator reset",
                new_password="replacement that must not win"),
                Request({"type": "http", "method": "PUT", "path": "/management-auth/me/password",
                         "headers": [], "client": ("127.0.0.1", 1234)}), snapshot, stale)
            raise AssertionError("Stale password update won")
        except HTTPException as error:
            assert error.status_code == 409
    with engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA review_legacy"))
        connection.execute(text("SET LOCAL search_path TO review_legacy"))
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, password_hash TEXT)"))
        connection.execute(text("INSERT INTO users VALUES (1, 'unchanged')"))
        connection.execute(text("CREATE TABLE conversation_messages (id INTEGER, app_id INTEGER, conversation_id TEXT)"))
        migrate(connection)
        migrate(connection)
        assert connection.execute(text("SELECT password_hash, must_change_password, temporary_password_expires_at FROM users")).one() == ("unchanged", False, None)
    print("Backend container/PostgreSQL checks passed: startup, HTTP setup lifecycle, protected boundaries, committed reset race and idempotent legacy migration.")


if __name__ == "__main__":
    main()
