import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from nemo_mcp_guardrails.database.models import Base


DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://"
    "nemo_mcp_guardrails:"
    "nemo_mcp_guardrails_dev_password"
    "@localhost:5432/"
    "nemo_mcp_guardrails"
)


def get_database_url() -> str:
    """Return the configured SQLAlchemy database URL."""

    load_dotenv()
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Yield one SQLAlchemy session for FastAPI request handling."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    """Return whether the database accepts a simple query."""

    with engine.connect() as connection:
        connection.execute(text("select 1"))

    return True


def create_database_tables() -> None:
    """Create database tables for the current prototype models."""

    Base.metadata.create_all(bind=engine)
