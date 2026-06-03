from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.allowed_test_cases import router as allowed_test_cases_router
from nemo_mcp_guardrails.api.policies import router as policies_router
from nemo_mcp_guardrails.database.connection import create_database_tables, get_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create prototype database tables before serving requests."""

    create_database_tables()
    yield


app = FastAPI(
    title="NeMo MCP Guardrails API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(allowed_test_cases_router)
app.include_router(policies_router)


@app.get("/")
def root() -> dict[str, str]:
    """Return a welcome message at the root endpoint."""

    return {"message": "Welcome to the NeMo MCP Guardrails API!"}

@app.get("/health")
def health() -> dict[str, str]:
    """Return a basic application health response."""

    return {"status": "ok"}


@app.get("/health/db")
def database_health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Return whether the API can reach the configured database."""

    db.execute(text("select 1"))
    return {"status": "ok", "database": "reachable"}
