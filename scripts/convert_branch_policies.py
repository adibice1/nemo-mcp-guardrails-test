"""Preview and explicitly approve legacy branch-policy conversion on a restored DB."""

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re

from _bootstrap import bootstrap_src
bootstrap_src()

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from nemo_mcp_guardrails.database.models import AppPolicyAssignmentRecord, GlobalPolicyAssignmentRecord, PolicyRecord
from nemo_mcp_guardrails.input_conditions import prepare_input_conditions
from nemo_mcp_guardrails.policy_rule_service import refresh_compiled_policy_rule, to_input_policy_object
from nemo_mcp_guardrails.resource_conditions import UnsupportedResourceCondition


class ConversionEntry(BaseModel):
    """Bind one explicit approval to the inventoried definition and assignments."""

    model_config = ConfigDict(extra="forbid", strict=True)
    policy_id: int = Field(gt=0)
    fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    proposed_conditions: dict | None
    approved: bool = False


class ConversionManifest(BaseModel):
    """Keep conversion decisions separate from read-only inventory."""

    model_config = ConfigDict(extra="forbid", strict=True)
    format: str = Field(pattern=r"^branch-policy-conversion-v1$")
    entries: list[ConversionEntry]


def proposed_selector(value: object) -> str | None:
    """Recognize only the reviewed legacy branch phrases, never guess aliases."""
    if not isinstance(value, str):
        return None
    token = r"([A-Za-z0-9_./-]+)"
    negative = re.fullmatch(rf"(?:any\s+)?(?:non\s+|not\s+){token}(?:\s+branch)?\s+to\s+{token}(?:\s+branch)?", value.strip())
    if negative:
        source, target = negative.groups()
        return f"source_branch != {json.dumps(source)} AND target_branch = {json.dumps(target)}"
    target_only = re.fullmatch(rf"any source branch to {token}(?:\s+branch)?", value.strip())
    if target_only:
        return f"target_branch = {json.dumps(target_only[1])}"
    return None


def inventory(db: Session, *, lock: bool = False) -> ConversionManifest:
    """Include exact definitions and assignment scope in each opaque fingerprint."""
    query = select(PolicyRecord).where(PolicyRecord.policy_type == "input").order_by(PolicyRecord.id)
    policies = list(db.scalars(query.with_for_update() if lock else query))
    entries = []
    for policy in policies:
        if not isinstance(policy.conditions, dict) or set(policy.conditions) != {"custom_resource"}:
            continue
        candidate = proposed_selector((policy.conditions or {}).get("custom_resource")) if isinstance(policy.conditions, dict) else None
        if candidate is None:
            continue
        obj = to_input_policy_object(policy)
        if (obj.connector, obj.resource, obj.action) not in {
            ("github", "pull_request", "create"), ("github", "pull_request", "merge"),
        }:
            continue
        scope = []
        for model in (AppPolicyAssignmentRecord, GlobalPolicyAssignmentRecord):
            assignments = select(model).where(model.policy_id == policy.id).order_by(model.id)
            for row in db.scalars(assignments.with_for_update() if lock else assignments):
                scope.append({column.name: getattr(row, column.name) for column in model.__table__.columns})
        metadata = {column.name: getattr(policy, column.name) for column in PolicyRecord.__table__.columns}
        metadata["assignments"] = scope
        metadata["resolved"] = (obj.connector, obj.action, obj.resource, obj.effect)
        digest = hashlib.sha256(json.dumps(metadata, sort_keys=True, default=str).encode()).hexdigest()
        try:
            prepared = prepare_input_conditions(replace(obj, custom_resource=candidate), {"custom_resource": candidate})
        except UnsupportedResourceCondition:
            prepared = None
        entries.append(ConversionEntry(policy_id=policy.id, fingerprint=digest, proposed_conditions=prepared))
    return ConversionManifest(format="branch-policy-conversion-v1", entries=entries)


def convert(db: Session, manifest: ConversionManifest, *, apply: bool = False) -> dict:
    """Validate all decisions before changing definitions, versions or artifacts."""
    current = {entry.policy_id: entry for entry in inventory(db, lock=apply).entries}
    seen = set()
    selected = []
    for entry in manifest.entries:
        expected = current.get(entry.policy_id)
        if entry.policy_id in seen or expected is None or entry.model_dump(exclude={"approved"}) != expected.model_dump(exclude={"approved"}):
            raise ValueError("Duplicate, changed or unknown conversion entry; regenerate the manifest.")
        seen.add(entry.policy_id)
        if entry.approved:
            if entry.proposed_conditions is None:
                raise ValueError("An unsupported conversion cannot be approved.")
            selected.append(entry)
    if apply:
        for entry in selected:
            policy = db.get(PolicyRecord, entry.policy_id)
            policy.conditions = entry.proposed_conditions
            policy.policy_version += 1
            refresh_compiled_policy_rule(db, policy)
        db.flush()
    return {"applied": apply, "converted_policy_ids": [entry.policy_id for entry in selected],
            "unapproved_entries": len(manifest.entries) - len(selected)}


def main() -> None:
    """Refuse production writes; default invocation never opens a database."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", action="store_true", help="Read configured policies and output a review manifest.")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--apply-rehearsal", action="store_true")
    args = parser.parse_args()
    if not args.database and args.manifest is None:
        if args.apply_rehearsal:
            parser.error("Applying requires --manifest.")
        parser.print_help()
        return
    if args.apply_rehearsal and args.manifest is None:
        parser.error("Applying requires --manifest.")
    from nemo_mcp_guardrails.database.connection import engine
    if args.apply_rehearsal and (engine.dialect.name != "postgresql" or not (engine.url.database or "").startswith("nemo_restore_check_")):
        parser.error("Writes are restricted to a nemo_restore_check_* PostgreSQL rehearsal database.")
    try:
        with Session(engine) as db, db.begin():
            if not args.apply_rehearsal and engine.dialect.name == "postgresql":
                from sqlalchemy import text
                db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
            result = (convert(db, ConversionManifest.model_validate_json(args.manifest.read_text(encoding="utf-8")), apply=args.apply_rehearsal)
                      if args.manifest else inventory(db).model_dump())
        print(json.dumps(result, indent=2))
    except Exception:
        parser.exit(2, "Conversion stopped; verify database state and regenerate the reviewed manifest. No private values are shown.\n")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
