import os
from datetime import datetime, timezone
from unittest.mock import patch

from _bootstrap import bootstrap_src

bootstrap_src()


def main() -> None:
    """Verify real JWT permissions and log queries using an isolated database."""
    settings = {
        "PYTHON_DOTENV_DISABLED": "1",
        "DATABASE_URL": "sqlite://",
        "GMS_JWT_SECRET": "runtime-log-test-secret-at-least-32-characters",
        "GMS_JWT_EXPIRY_MINUTES": "10",
    }
    with patch.dict(os.environ, settings):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        from nemo_mcp_guardrails.api.runtime_logs import router
        from nemo_mcp_guardrails.database.connection import get_db
        from nemo_mcp_guardrails.database.models import (
            AppRecord,
            Base,
            LlmConfigRecord,
            RuntimeLogEventRecord,
            RuntimeUserLogRecord,
            RuntimeLogRecord,
            UserRecord,
        )
        from nemo_mcp_guardrails.management_auth import create_access_token

        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        with engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(engine, tables=[
            UserRecord.__table__,
            LlmConfigRecord.__table__,
            AppRecord.__table__,
            RuntimeLogRecord.__table__,
            RuntimeLogEventRecord.__table__,
            RuntimeUserLogRecord.__table__,
        ])
        app = FastAPI()
        app.include_router(router)

        def test_db():
            """Use the disposable database without overriding authentication."""
            with sessions() as db:
                yield db

        app.dependency_overrides[get_db] = test_db
        timestamp = datetime.now(timezone.utc)
        first_id, second_id, anonymous_id = "a" * 32, "b" * 32, "c" * 32

        try:
            with sessions() as db:
                users = [
                    UserRecord(
                        email=f"{label}@example.com",
                        name=label,
                        username=label,
                        password_hash="private-password-hash-canary",
                        system_role=role,
                        enabled=enabled,
                    )
                    for label, role, enabled in [
                        ("admin", "admin", True),
                        ("developer", "developer", True),
                        ("disabled", "admin", False),
                    ]
                ]
                apps = [
                    AppRecord(
                        name=f"App {index}",
                        client_id=f"log-test-{index}",
                        api_key_hash="private-api-key-hash-canary",
                    )
                    for index in (1, 2)
                ]
                db.add_all(users + apps)
                db.flush()
                app_ids = [record.id for record in apps]
                admin_id = users[0].id
                headers = [
                    {"Authorization": f"Bearer {create_access_token(user)}"}
                    for user in users
                ]
                for request_id, app_id, outcome in [
                    (first_id, app_ids[0], "passed"),
                    (second_id, app_ids[1], "blocked"),
                    (anonymous_id, None, "rejected"),
                ]:
                    record = RuntimeLogRecord(
                        request_id=request_id,
                        app_id=app_id,
                        started_at=timestamp,
                        completed_at=timestamp,
                        http_status=401 if outcome == "rejected" else 200,
                        outcome=outcome,
                        duration_ms=10,
                    )
                    if request_id != anonymous_id:
                        record.user_log = RuntimeUserLogRecord(
                            conversation_id="shared-conversation",
                            input_text=f"private-input-{request_id}",
                            response_text=f"private-response-{request_id}",
                        )
                    record.events = [
                        RuntimeLogEventRecord(
                            sequence=sequence,
                            timestamp=timestamp,
                            event=event,
                            severity="INFO",
                            stage="request",
                            outcome=event_outcome,
                        )
                        for sequence, event, event_outcome in [
                            (2, "request.completed", outcome),
                            (1, "request.received", "started"),
                        ]
                    ]
                    db.add(record)
                db.commit()

            admin, developer, disabled = headers
            with TestClient(app) as client:
                for url in ["/runtime-logs", f"/runtime-logs/{first_id}", f"/runtime-logs/{first_id}/user-content"]:
                    for credentials, expected in [
                        ({}, 401),
                        ({"Authorization": "Bearer invalid-token"}, 401),
                        ({"X-App-ID": "log-test-1", "X-API-Key": "fake"}, 401),
                        (developer, 403),
                        (disabled, 401),
                    ]:
                        response = client.get(url, headers=credentials)
                        assert response.status_code == expected, response.text

                response = client.get("/runtime-logs", headers=admin)
                assert response.status_code == 200, response.text
                assert response.headers["cache-control"] == "no-store"
                assert [item["request_id"] for item in response.json()["items"]] == [
                    anonymous_id, second_id, first_id,
                ]
                assert response.json()["items"][0]["app_id"] is None
                assert "private-" not in response.text
                assert all("events" not in item for item in response.json()["items"])

                for offset, expected_id, has_more in [
                    (0, anonymous_id, True),
                    (1, second_id, True),
                    (2, first_id, False),
                ]:
                    page = client.get(
                        "/runtime-logs",
                        headers=admin,
                        params={"limit": 1, "offset": offset},
                    ).json()
                    assert page["items"][0]["request_id"] == expected_id
                    assert page["has_more"] is has_more

                for filters, expected_ids in [
                    ({"app_id": app_ids[0]}, [first_id]),
                    ({"outcome": "blocked"}, [second_id]),
                    ({"app_id": app_ids[0], "outcome": "blocked"}, []),
                    ({"offset": 10}, []),
                ]:
                    page = client.get(
                        "/runtime-logs", headers=admin, params=filters,
                    ).json()
                    assert [item["request_id"] for item in page["items"]] == expected_ids

                for invalid in [
                    {"limit": 0}, {"limit": 101}, {"offset": -1},
                    {"offset": 10001}, {"app_id": 0}, {"outcome": "unknown"},
                    {"user_content_only": "invalid"},
                ]:
                    assert client.get(
                        "/runtime-logs", headers=admin, params=invalid,
                    ).status_code == 422

                for filters, expected_ids, has_more in [
                    ({}, [second_id, first_id], False),
                    ({"limit": 1}, [second_id], True),
                    ({"limit": 1, "offset": 1}, [first_id], False),
                    ({"app_id": app_ids[0]}, [first_id], False),
                    ({"outcome": "blocked"}, [second_id], False),
                    ({"outcome": "rejected"}, [], False),
                    ({"app_id": app_ids[0], "outcome": "blocked"}, [], False),
                    ({"offset": 10}, [], False),
                ]:
                    response = client.get(
                        "/runtime-logs", headers=admin,
                        params={"user_content_only": True, **filters},
                    )
                    assert response.status_code == 200, response.text
                    assert response.headers["cache-control"] == "no-store"
                    page = response.json()
                    assert [item["request_id"] for item in page["items"]] == expected_ids
                    assert page["has_more"] is has_more
                    assert "private-" not in response.text

                detail = client.get(f"/runtime-logs/{first_id}", headers=admin)
                assert detail.status_code == 200, detail.text
                assert detail.headers["cache-control"] == "no-store"
                assert [event["sequence"] for event in detail.json()["events"]] == [1, 2]
                assert "private-" not in detail.text
                assert client.get(
                    f"/runtime-logs/{'0' * 32}", headers=admin,
                ).status_code == 404
                assert client.get(
                    "/runtime-logs/not-a-request-id", headers=admin,
                ).status_code == 422

                content = client.get(f"/runtime-logs/{first_id}/user-content", headers=admin)
                assert content.status_code == 200, content.text
                assert content.headers["cache-control"] == "no-store"
                assert content.json() == dict(
                    request_id=first_id, conversation_id="shared-conversation",
                    input_text=f"private-input-{first_id}",
                    response_text=f"private-response-{first_id}",
                )
                for missing in [anonymous_id, "0" * 32]:
                    assert client.get(f"/runtime-logs/{missing}/user-content", headers=admin).status_code == 404
                with sessions() as db:
                    db.get(UserRecord, admin_id).system_role = "developer"
                    db.commit()
                assert client.get("/runtime-logs", headers=admin).status_code == 403
                with sessions() as db:
                    db.get(UserRecord, admin_id).enabled = False
                    db.commit()
                assert client.get("/runtime-logs", headers=admin).status_code == 401
            from pathlib import Path
            from runpy import run_path
            cleanup = run_path(str(Path(__file__).resolve().parents[1] / "scripts/cleanup_runtime_logs.py"))["cleanup"]
            with sessions.begin() as db:
                db.get(RuntimeLogRecord, first_id).completed_at = timestamp.replace(year=2020)
                db.get(RuntimeLogRecord, anonymous_id).completed_at = None
            with sessions.begin() as db:
                assert cleanup(db, timestamp.replace(year=2020), True) == 0
                assert cleanup(db, timestamp) == 1
                assert db.query(RuntimeLogRecord).count() == 3
                assert db.query(RuntimeUserLogRecord).count() == 2
                assert cleanup(db, timestamp, True) == 1
            with sessions.begin() as db:
                assert {row.request_id for row in db.query(RuntimeLogRecord)} == {second_id, anonymous_id}
                assert db.query(RuntimeLogEventRecord).filter_by(request_id=first_id).count() == 0
                assert db.query(RuntimeLogEventRecord).count() == 4
                assert db.get(RuntimeUserLogRecord, first_id) is None
                assert db.query(RuntimeUserLogRecord).count() == 1
                assert db.get(RuntimeUserLogRecord, second_id).input_text == f"private-input-{second_id}"
                assert cleanup(db, timestamp, True) == 0
        finally:
            app.dependency_overrides.clear()
            engine.dispose()

    print("Runtime log authentication, pagination, filtering and detail checks passed.")


if __name__ == "__main__":
    main()
