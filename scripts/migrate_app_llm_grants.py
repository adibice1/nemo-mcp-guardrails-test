"""Preview grant storage and explicitly reviewed current-selection grants."""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Literal

from _bootstrap import bootstrap_src

bootstrap_src()

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import inspect, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateIndex, CreateTable

from nemo_mcp_guardrails.database.models import (
    AppLlmGrantRecord, AppRecord, LlmConfigRecord,
)


class GrantCandidate(BaseModel):
    """Require an explicit decision bound to one inventoried selection."""

    model_config = ConfigDict(extra="forbid", strict=True)

    app_id: int = Field(gt=0)
    client_id: str
    app_name: str
    purpose: Literal["main", "guardrail"]
    llm_config_id: int | None = Field(ge=1)
    config_name: str | None
    config_enabled: bool | None
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    enabled: bool


class GrantManifest(BaseModel):
    """Reject unknown fields and unsupported manifest formats."""

    model_config = ConfigDict(extra="forbid", strict=True)

    format: Literal["app-llm-grants-v1"]
    entries: list[GrantCandidate]


def inventory(
    db: Session, *, app_ids: set[int] | None = None, lock: bool = False,
) -> GrantManifest:
    """Inventory selections with approval off, without reading credential values."""

    query = select(AppRecord).order_by(AppRecord.id)
    if app_ids is not None:
        query = query.where(AppRecord.id.in_(app_ids))
    apps = list(db.scalars(query.with_for_update() if lock else query))
    config_ids = {
        config_id for app in apps
        for config_id in (app.main_llm_config_id, app.guardrail_llm_config_id)
        if config_id is not None
    }
    query = select(LlmConfigRecord).where(
        LlmConfigRecord.id.in_(config_ids),
    ).order_by(LlmConfigRecord.id)
    configs = {
        row.id: row for row in db.scalars(query.with_for_update() if lock else query)
    }
    defaults = {
        name: os.getenv(name, "") for name in (
            "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT", "AZURE_OPENAI_API_VERSION",
        )
    }
    entries = []
    for app in apps:
        for purpose, config_id in (
            ("main", app.main_llm_config_id), ("guardrail", app.guardrail_llm_config_id),
        ):
            config = configs.get(config_id)
            if config_id is not None and config is None:
                raise ValueError("A selected configuration is missing.")
            metadata = {
                "app_id": app.id, "client_id": app.client_id, "app_name": app.name,
                "authorized": app.authorized, "purpose": purpose, "defaults": defaults,
                "config": None if config is None else {
                    name: getattr(config, name) for name in (
                        "id", "name", "provider", "model_name", "endpoint",
                        "credential_reference", "enabled",
                    )
                },
            }
            digest = hashlib.sha256(
                json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            entries.append(GrantCandidate(
                app_id=app.id, client_id=app.client_id, app_name=app.name,
                purpose=purpose, llm_config_id=config_id,
                config_name=config.name if config else None,
                config_enabled=config.enabled if config else None,
                fingerprint=digest, enabled=False,
            ))
    return GrantManifest(format="app-llm-grants-v1", entries=entries)


def seed_manifest(db: Session, manifest: GrantManifest, *, apply: bool = False) -> dict:
    """Validate the whole manifest before adding grants; never change existing ones."""

    current = inventory(db, app_ids={entry.app_id for entry in manifest.entries}, lock=apply)
    candidates = {(entry.app_id, entry.purpose): entry for entry in current.entries}
    has_table = inspect(db.connection()).has_table(AppLlmGrantRecord.__tablename__)
    if apply and not has_table:
        raise ValueError("Create the grant table before applying a manifest.")
    seen = set()
    pending = []
    existing_count = 0
    for entry in manifest.entries:
        key = (entry.app_id, entry.purpose)
        if key in seen:
            raise ValueError("Duplicate app/purpose manifest entry.")
        seen.add(key)
        expected = candidates.get(key)
        if expected is None or entry.model_dump(exclude={"enabled"}) != expected.model_dump(
            exclude={"enabled"},
        ):
            raise ValueError("Manifest selection metadata is stale or unknown.")
        if entry.enabled and entry.config_enabled is False:
            raise ValueError("A disabled configuration cannot receive an enabled grant.")
        query = select(AppLlmGrantRecord).where(
            AppLlmGrantRecord.app_id == entry.app_id,
            AppLlmGrantRecord.purpose == entry.purpose,
            AppLlmGrantRecord.llm_config_id == entry.llm_config_id,
        )
        existing = (
            db.scalars(query.with_for_update() if apply else query).one_or_none()
            if has_table else None
        )
        if existing is not None:
            if existing.enabled != entry.enabled:
                raise ValueError("Existing grants require an explicit management operation.")
            existing_count += 1
        elif entry.enabled:
            pending.append(AppLlmGrantRecord(
                app_id=entry.app_id, purpose=entry.purpose,
                llm_config_id=entry.llm_config_id, enabled=True,
            ))
    if apply:
        db.add_all(pending)
        db.flush()
    return {
        "applied": apply, "new_grants": len(pending), "existing_grants": existing_count,
        "unapproved_entries": sum(not entry.enabled for entry in manifest.entries),
    }


def main(argv: list[str] | None = None) -> None:
    """Preview by default; separate schema creation from reviewed grant seeding."""

    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--apply-schema", action="store_true", help="Create only the grant table.")
    actions.add_argument("--apply-manifest", action="store_true", help="Seed a reviewed manifest.")
    parser.add_argument("--manifest", type=Path, help="Reviewed inventory JSON; preview unless applied.")
    args = parser.parse_args(argv)
    if args.apply_manifest and args.manifest is None:
        parser.error("--apply-manifest requires --manifest")
    if args.apply_schema and args.manifest is not None:
        parser.error("Schema creation and manifest processing are separate actions")

    try:
        from nemo_mcp_guardrails.database.connection import engine

        if engine.dialect.name not in {"postgresql", "sqlite"}:
            raise ValueError("Unsupported grant migration database dialect.")
        if args.manifest is not None:
            manifest = GrantManifest.model_validate_json(args.manifest.read_text(encoding="utf-8"))
            with Session(engine) as db, db.begin():
                result = seed_manifest(db, manifest, apply=args.apply_manifest)
            print(json.dumps(result, indent=2))
            return
        table = AppLlmGrantRecord.__table__
        print(str(CreateTable(table).compile(engine)), file=sys.stderr)
        for index in sorted(table.indexes, key=lambda item: item.name):
            print(str(CreateIndex(index).compile(engine)), file=sys.stderr)
        if args.apply_schema:
            with engine.begin() as connection:
                table.create(connection, checkfirst=True)
        with Session(engine) as db:
            manifest = inventory(db)
        print(manifest.model_dump_json(indent=2))
    except (ValueError, OSError, SQLAlchemyError):
        parser.exit(2, "Grant migration stopped: invalid manifest or database state; no credentials are shown.\n")


if __name__ == "__main__":
    main()
