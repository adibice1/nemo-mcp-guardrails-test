"""Preview or apply one explicitly selected user/app developer link."""

import argparse
from _bootstrap import bootstrap_src
bootstrap_src()

from sqlalchemy import select
from nemo_mcp_guardrails.database.models import AppRecord, AppUserRecord, UserRecord


def backfill_link(db, user_id: int, app_id: int, *, apply: bool = False) -> bool:
    """Return whether a link is needed; retain every existing membership unchanged."""
    user, app = db.get(UserRecord, user_id), db.get(AppRecord, app_id)
    if user is None or not user.enabled or app is None or not app.authorized:
        raise ValueError("Select an enabled user and an authorized app.")
    existing = db.scalar(select(AppUserRecord).where(
        AppUserRecord.user_id == user_id, AppUserRecord.app_id == app_id,
    ))
    if existing is not None:
        return False
    if apply:
        db.add(AppUserRecord(user_id=user_id, app_id=app_id, role="admin"))
        db.flush()
    return True


def main() -> None:
    """Require exact IDs and default to a read-only preview."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--app-id", type=int, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.user_id <= 0 or args.app_id <= 0:
        parser.error("IDs must be positive")
    from nemo_mcp_guardrails.database.connection import SessionLocal
    with SessionLocal() as db:
        needed = backfill_link(db, args.user_id, args.app_id, apply=args.apply)
        if args.apply:
            db.commit()
    print(f"Target user={args.user_id}, app={args.app_id}: " +
          ("linked" if args.apply and needed else "would link" if needed else "already linked"))


if __name__ == "__main__":
    main()
