import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.api.allowed_test_cases import router as allowed_test_cases_router
from nemo_mcp_guardrails.api.apps import router as apps_router
from nemo_mcp_guardrails.api.global_policy_assignments import (
    router as global_policy_assignments_router,
)
from nemo_mcp_guardrails.api.llm_configs import router as llm_configs_router
from nemo_mcp_guardrails.api.management_auth import router as management_auth_router
from nemo_mcp_guardrails.api.policies import router as policies_router
from nemo_mcp_guardrails.api.policy_metadata import router as policy_metadata_router
from nemo_mcp_guardrails.api.policy_assignment_resolution import (
    router as policy_assignment_resolution_router,
)
from nemo_mcp_guardrails.api.runtime import router as runtime_router
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

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "NEMO_CORS_ORIGINS",
        "http://127.0.0.1:3000,http://localhost:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(allowed_test_cases_router)
app.include_router(apps_router)
app.include_router(global_policy_assignments_router)
app.include_router(llm_configs_router)
app.include_router(management_auth_router)
app.include_router(policies_router)
app.include_router(policy_metadata_router)
app.include_router(policy_assignment_resolution_router)
app.include_router(runtime_router)


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
