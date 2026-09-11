import argparse
from datetime import datetime, timedelta, timezone
from _bootstrap import bootstrap_src

bootstrap_src()

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from nemo_mcp_guardrails.database.connection import SessionLocal
from nemo_mcp_guardrails.database.models import RuntimeLogRecord


def cleanup(db, cutoff, apply=False):
    """Inspect or delete one bounded batch of expired completed requests."""
    query = select(RuntimeLogRecord).where(
        RuntimeLogRecord.completed_at < cutoff
    ).order_by(RuntimeLogRecord.completed_at, RuntimeLogRecord.request_id)
    query = query.limit(500).options(selectinload(RuntimeLogRecord.events))
    if apply:
        query = query.with_for_update()
    records = list(db.scalars(query))
    if apply:
        for record in records:
            db.delete(record)
    return len(records)


def main():
    """Default to a read-only preview against the configured database."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, choices=range(1, 3651), default=30, metavar="1-3650")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    with SessionLocal.begin() as db:
        count = cleanup(db, cutoff, args.apply)
    mode = "Deleted" if args.apply else "Would delete"
    print(f"{mode} {count} requests before {cutoff.isoformat()} (batch cap: 500).")


if __name__ == "__main__":
    main()
