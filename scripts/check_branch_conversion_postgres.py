"""Disposable PostgreSQL 18 rehearsal of the approved conversion helper."""
import os
import time
from unittest.mock import patch

from _bootstrap import bootstrap_src
bootstrap_src()
from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
import convert_branch_policies as conversion
from nemo_mcp_guardrails.database.models import Base, AppRecord, PolicyRecord, AppPolicyAssignmentRecord, GlobalPolicyAssignmentRecord, CompiledPolicyRuleRecord
from nemo_mcp_guardrails.database.runtime_policy_snapshot import read_runtime_policy_snapshot
def main() -> None:
    """Require the isolated empty review DB before creating any fixture tables."""
    url = make_url(os.environ["DATABASE_URL"])
    if url.host != "reviewdb" or url.database != "nemo_restore_check_patch019" or os.environ.get("PYTHON_DOTENV_DISABLED") != "1":
        raise RuntimeError("Disposable review environment required")
    engine = create_engine(url)
    for attempt in range(30):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            break
        except Exception:
            if attempt == 29:
                raise
            time.sleep(0.2)
    with engine.connect() as connection:
        version = connection.scalar(text("SHOW server_version"))
        assert version.startswith("18."), version
    if inspect(engine).get_table_names():
        raise RuntimeError("An empty disposable database is required")
    Base.metadata.create_all(engine)
    with Session(engine) as db, db.begin():
        assert db.scalar(select(func.count(PolicyRecord.id))) == 0
        db.add_all([AppRecord(id=i, name=f"Review {i}", client_id=f"review-{i}", api_key_hash="unused") for i in (4, 208, 214)])
        for policy_id, action, selector in (
            (181, "create", "not development branch to staging branch"),
            (182, "merge", "any source branch to main branch"),
            (192, "create", "any non staging branch to production branch"),
            (193, "merge", "any non staging branch to production branch"),
            (209, "create", "non development to staging"),
        ):
            db.add(PolicyRecord(id=policy_id, policy_type="input", connector="github", action=action,
                                resource="pull_request", conditions={"custom_resource": selector}))
        db.flush()
        db.add_all([GlobalPolicyAssignmentRecord(policy_id=209, display_name="Global route"),
                    AppPolicyAssignmentRecord(app_id=4, policy_id=192, display_name="App route"),
                    AppPolicyAssignmentRecord(app_id=208, policy_id=193, display_name="Merge route")])
    with Session(engine) as db:
        manifest = conversion.inventory(db)
        assert len(manifest.entries) == 5
        approved = manifest.model_copy(update={"entries": [entry.model_copy(update={"approved": True}) for entry in manifest.entries]})
        assert not conversion.convert(db, approved)["applied"]
    with Session(engine) as db, db.begin():
        db.scalar(select(GlobalPolicyAssignmentRecord)).display_name = "Reviewed global label"
    try:
        with Session(engine) as db, db.begin():
            conversion.convert(db, approved, apply=True)
    except ValueError:
        pass
    else:
        raise AssertionError("Changed assignment scope accepted")
    with Session(engine) as db:
        approved = conversion.inventory(db)
        approved = approved.model_copy(update={"entries": [entry.model_copy(update={"approved": True}) for entry in approved.entries]})
    original_refresh = conversion.refresh_compiled_policy_rule
    counter = 0
    def fail_second(db, policy):
        """Force a real partial write before checking transaction rollback."""
        nonlocal counter
        counter += 1
        if counter == 2:
            raise RuntimeError("Injected transactional failure")
        result = original_refresh(db, policy)
        db.flush()
        return result
    try:
        with patch.object(conversion, "refresh_compiled_policy_rule", side_effect=fail_second):
            with Session(engine) as db, db.begin():
                conversion.convert(db, approved, apply=True)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Injected failure did not occur")
    with Session(engine) as db:
        assert all(row.policy_version == 1 for row in db.scalars(select(PolicyRecord)))
        assert db.scalar(select(func.count(CompiledPolicyRuleRecord.id))) == 0
    with Session(engine) as db, db.begin():
        result = conversion.convert(db, approved, apply=True)
        assert result["converted_policy_ids"] == [181, 182, 192, 193, 209]
    with Session(engine) as db:
        rows = list(db.scalars(select(PolicyRecord)))
        assert len(rows) == 5 and all(row.enabled and row.policy_version == 2 for row in rows)
        assert db.scalar(select(func.count(CompiledPolicyRuleRecord.id))) == 5
        assert db.scalar(select(GlobalPolicyAssignmentRecord)).display_name == "Reviewed global label"
        assert db.scalar(select(AppPolicyAssignmentRecord).where(AppPolicyAssignmentRecord.app_id == 4)).display_name == "App route"
        assert {entry.policy_id for entry in read_runtime_policy_snapshot(db, 4).policies} == {192, 209}
        assert {entry.policy_id for entry in read_runtime_policy_snapshot(db, 214).policies} == {209}
        assert not conversion.inventory(db).entries
    print("PostgreSQL", version, "passed: preview, stale-assignment rejection, actual-write rollback, five conversions, labels/assignments and scoped runtime snapshots.")
    engine.dispose()


if __name__ == "__main__":
    main()
