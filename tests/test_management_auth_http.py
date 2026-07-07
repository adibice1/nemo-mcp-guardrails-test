import os
from uuid import uuid4

from _bootstrap import bootstrap_src

bootstrap_src()

from fastapi.testclient import TestClient
from sqlalchemy import select

from migrate_management_auth import migrate_management_auth_schema
from nemo_mcp_guardrails.api.main import app
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import UserRecord
from nemo_mcp_guardrails.management_auth import hash_password


def main() -> None:
    """Verify login, disabled signup, JWT identity, and rejection behavior."""

    os.environ["GMS_JWT_SECRET"] = "test-management-secret-with-at-least-32-characters"
    os.environ["GMS_JWT_EXPIRY_MINUTES"] = "60"
    migrate_management_auth_schema()

    email = f"management-{uuid4().hex}@example.com"
    password = "a-valid-test-password"

    try:
        with SessionLocal() as db:
            user = UserRecord(
                email=email,
                name=email,
                username=email,
                password_hash=hash_password(password),
                system_role="developer",
                enabled=True,
            )
            db.add(user)
            db.commit()

        with TestClient(app) as client:
            disabled_signup = client.post(
                "/management-auth/signup",
                json={
                    "email": f"new-{email}",
                    "password": password,
                },
            )
            assert disabled_signup.status_code == 403, disabled_signup.text

            wrong_password = client.post(
                "/management-auth/login",
                json={"email": email, "password": "wrong-password"},
            )
            assert wrong_password.status_code == 401, wrong_password.text

            login = client.post(
                "/management-auth/login",
                json={"email": email, "password": password},
            )
            assert login.status_code == 200, login.text
            token = login.json()["access_token"]

            missing_token = client.get("/management-auth/me")
            assert missing_token.status_code == 401, missing_token.text

            invalid_token = client.get(
                "/management-auth/me",
                headers={"Authorization": "Bearer invalid-token"},
            )
            assert invalid_token.status_code == 401, invalid_token.text

            current_user = client.get(
                "/management-auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert current_user.status_code == 200, current_user.text
            assert current_user.json()["email"] == email

            updated_profile = client.put(
                "/management-auth/me",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": "Test Developer", "username": f"user-{uuid4().hex}"},
            )
            assert updated_profile.status_code == 200, updated_profile.text
            assert updated_profile.json()["name"] == "Test Developer"
            assert updated_profile.json()["username"].startswith("user-")

        with SessionLocal() as db:
            user = db.scalar(select(UserRecord).where(UserRecord.email == email))
            assert user is not None
            assert user.password_hash != password
            assert user.password_hash.startswith("scrypt$")
    finally:
        with SessionLocal() as db:
            user = db.scalar(select(UserRecord).where(UserRecord.email == email))
            if user is not None:
                db.delete(user)
                db.commit()

    print("Management authentication HTTP checks passed.")
    print("- Public signup is disabled for admin-managed accounts.")
    print("- Login and /me accept only valid bearer tokens.")
    print("- Authenticated users can save name and username profile fields.")


if __name__ == "__main__":
    main()
