import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

from nemo_mcp_guardrails.database.models import UserRecord


JWT_ALGORITHM = "HS256"
PASSWORD_SCHEME = "scrypt"


def normalize_email(email: str) -> str:
    """Return the canonical form used for management-user emails."""

    return email.strip().lower()


def hash_password(password: str) -> str:
    """Hash one password with scrypt and a random salt."""

    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=64,
    )
    return "$".join(
        (
            PASSWORD_SCHEME,
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        )
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    """Verify one password against a stored scrypt hash."""

    try:
        scheme, encoded_salt, encoded_digest = encoded_hash.split("$", 2)
        if scheme != PASSWORD_SCHEME:
            return False
        salt = base64.urlsafe_b64decode(encoded_salt.encode("ascii"))
        expected_digest = base64.urlsafe_b64decode(encoded_digest.encode("ascii"))
    except (ValueError, UnicodeError):
        return False

    actual_digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=len(expected_digest),
    )
    return hmac.compare_digest(actual_digest, expected_digest)


def _jwt_secret() -> str:
    """Load the required JWT signing secret."""

    load_dotenv()
    secret = os.getenv("GMS_JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("GMS_JWT_SECRET must contain at least 32 characters")
    return secret


def _jwt_expiry_minutes() -> int:
    """Return the configured positive management-token lifetime."""

    raw_value = os.getenv("GMS_JWT_EXPIRY_MINUTES", "480")
    try:
        value = int(raw_value)
    except ValueError as error:
        raise RuntimeError("GMS_JWT_EXPIRY_MINUTES must be an integer") from error
    if value <= 0:
        raise RuntimeError("GMS_JWT_EXPIRY_MINUTES must be positive")
    return value


def create_access_token(user: UserRecord) -> str:
    """Create a signed management access token for one user."""

    issued_at = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.system_role,
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=_jwt_expiry_minutes()),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    """Verify a management token and return its user ID."""

    payload = jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.isdigit():
        raise jwt.InvalidTokenError("Token subject is invalid")
    return int(subject)
