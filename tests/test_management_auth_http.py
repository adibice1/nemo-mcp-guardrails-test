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


def main() -> None:
    """Verify signup, login, JWT identity, and generic rejection behavior."""

    os.environ["GMS_JWT_SECRET"] = "test-management-secret-with-at-least-32-characters"
    os.environ["GMS_JWT_EXPIRY_MINUTES"] = "60"
    migrate_management_auth_schema()

    email = f"management-{uuid4().hex}@example.com"
    password = "a-valid-test-password"

    try:
        with TestClient(app) as client:
            role_injection = client.post(
                "/management-auth/signup",
                json={
                    "email": f"admin-{email}",
                    "password": password,
                    "system_role": "admin",
                },
            )
            assert role_injection.status_code == 422, role_injection.text

            signup = client.post(
                "/management-auth/signup",
                json={"email": email.upper(), "password": password},
            )
            assert signup.status_code == 201, signup.text
            session = signup.json()
            assert session["token_type"] == "bearer"
            assert session["user"]["email"] == email
            assert session["user"]["name"] == email
            assert session["user"]["username"] == email
            assert session["user"]["system_role"] == "developer"

            duplicate = client.post(
                "/management-auth/signup",
                json={"email": email, "password": password},
            )
            assert duplicate.status_code == 409, duplicate.text

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
    print("- Signup creates developer users with scrypt password hashes.")
    print("- Login and /me accept only valid bearer tokens.")
    print("- Authenticated users can save name and username profile fields.")
    print("- Duplicate accounts and role injection are rejected.")


if __name__ == "__main__":
    main()
